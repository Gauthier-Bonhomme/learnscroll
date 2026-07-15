"""
API LearnScroll — sert UNIQUEMENT du contenu déjà généré (zéro appel IA au feed).

Endpoints principaux :
  GET  /api/feed?user_id=...          feed vertical personnalisé
  GET  /api/cards/{id}                mode détail (body + couches 'pourquoi')
  POST /api/cards/{id}/why            approfondissement récursif (à la demande + cache)
  POST /api/interactions             journalise view/like/favorite/share/expand
  GET  /api/favorites?user_id=...     favoris
  GET  /api/recommendations/{id}      « Tu aimeras aussi »
  GET  /api/profile?user_id=...       streak, niveau, stats, séries complétées
  GET  /api/series                    catalogue des séries
  Admin CMS statique sous /admin
"""

from __future__ import annotations

import os

from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import gamification, personalization
from .db import Card, Interaction, SessionLocal, Series, init_db
from .why_service import deepen

app = FastAPI(title="LearnScroll API", version="0.1")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------------------------------- #
# Feed & détail                                                               #
# --------------------------------------------------------------------------- #
@app.get("/api/feed")
def feed(user_id: str = Query("anon"), limit: int = 10, db: Session = Depends(get_db)):
    cards = personalization.build_feed(db, user_id, limit)
    return {"cards": [c.to_feed() for c in cards]}


@app.get("/api/cards/{card_id}")
def card_detail(card_id: int, db: Session = Depends(get_db)):
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(404, "Carte introuvable")
    return card.to_detail()


@app.post("/api/cards/{card_id}/why")
def why_deeper(card_id: int, question: str = Body(..., embed=True), db: Session = Depends(get_db)):
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(404, "Carte introuvable")
    return deepen(db, card, question)


# --------------------------------------------------------------------------- #
# Interactions, favoris, recommandations                                      #
# --------------------------------------------------------------------------- #
@app.post("/api/interactions")
def log_interaction(
    user_id: str = Body("anon"),
    card_id: int = Body(...),
    kind: str = Body(...),
    dwell_ms: int = Body(0),
    db: Session = Depends(get_db),
):
    if kind not in {"view", "like", "favorite", "share", "expand"}:
        raise HTTPException(400, "kind invalide")
    if not db.get(Card, card_id):
        raise HTTPException(404, "Carte introuvable")
    db.add(Interaction(user_id=user_id, card_id=card_id, kind=kind, dwell_ms=dwell_ms))
    db.commit()
    return {"ok": True}


@app.get("/api/favorites")
def favorites(user_id: str = Query("anon"), db: Session = Depends(get_db)):
    ids = db.execute(
        select(Interaction.card_id)
        .where(Interaction.user_id == user_id, Interaction.kind == "favorite")
        .distinct()
    ).scalars().all()
    cards = db.execute(select(Card).where(Card.id.in_(ids or [-1]))).scalars().all()
    return {"cards": [c.to_feed() for c in cards]}


@app.get("/api/recommendations/{card_id}")
def recommendations(card_id: int, limit: int = 5, db: Session = Depends(get_db)):
    """« Tu aimeras aussi » : même catégorie, hors la carte courante."""
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(404, "Carte introuvable")
    similar = db.execute(
        select(Card)
        .where(Card.category == card.category, Card.id != card.id)
        .limit(limit)
    ).scalars().all()
    return {"cards": [c.to_feed() for c in similar]}


# --------------------------------------------------------------------------- #
# Gamification & séries                                                        #
# --------------------------------------------------------------------------- #
@app.get("/api/profile")
def profile(user_id: str = Query("anon"), db: Session = Depends(get_db)):
    return gamification.profile(db, user_id)


@app.get("/api/series")
def series(db: Session = Depends(get_db)):
    rows = db.execute(select(Series)).scalars().all()
    out = []
    for s in rows:
        count = db.execute(
            select(func.count(Card.id)).where(Card.series_id == s.id)
        ).scalar_one()
        out.append({"id": s.id, "name": s.name, "category": s.category, "cards": count})
    return {"series": out}


@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    total = db.execute(select(func.count(Card.id))).scalar_one()
    by_cat = db.execute(
        select(Card.category, func.count(Card.id)).group_by(Card.category)
    ).all()
    return {"total_cards": total, "by_category": {c: n for c, n in by_cat}}


# --------------------------------------------------------------------------- #
# Admin CMS (statique)                                                        #
# --------------------------------------------------------------------------- #
_ADMIN_DIR = os.path.join(os.path.dirname(__file__), "..", "admin_ui")
if os.path.isdir(_ADMIN_DIR):
    app.mount("/admin", StaticFiles(directory=_ADMIN_DIR, html=True), name="admin")


@app.get("/")
def root():
    return {"app": "LearnScroll", "docs": "/docs", "admin": "/admin",
            "webapp": "/app", "feed": "/api/feed"}


# App web (prototype du feed) — montée en dernier pour ne pas masquer /api.
_WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "webapp")
if os.path.isdir(_WEB_DIR):
    app.mount("/app", StaticFiles(directory=_WEB_DIR, html=True), name="webapp")
