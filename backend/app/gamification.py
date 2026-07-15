"""
Gamification : streak journalier, niveau utilisateur, statistiques, séries.
Calculé à la volée depuis la table interactions (aucun état à maintenir).
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import Card, Interaction

# Curieux -> Passionné -> Expert -> Sage, selon le nombre de cartes vues.
_LEVELS = [(0, "Curieux"), (25, "Passionné"), (100, "Expert"), (300, "Sage")]


def _active_days(session: Session, user_id: str) -> set[date]:
    rows = session.execute(
        select(Interaction.created_at).where(
            Interaction.user_id == user_id, Interaction.kind == "view"
        )
    ).all()
    return {r[0].date() for r in rows}


def current_streak(session: Session, user_id: str) -> int:
    days = _active_days(session, user_id)
    if not days:
        return 0
    today = date.today()
    # La série tient si l'utilisateur était actif aujourd'hui ou hier.
    cursor = today if today in days else today - timedelta(days=1)
    if cursor not in days:
        return 0
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _level(views: int) -> dict:
    name = _LEVELS[0][1]
    nxt = None
    for threshold, label in _LEVELS:
        if views >= threshold:
            name = label
        elif nxt is None:
            nxt = (threshold, label)
    return {"name": name, "views": views,
            "next": {"at": nxt[0], "name": nxt[1]} if nxt else None}


def completed_series(session: Session, user_id: str) -> list[str]:
    """Séries dont l'utilisateur a vu toutes les cartes présentes en base."""
    seen = session.execute(
        select(Card.series_id, func.count(Interaction.id))
        .join(Interaction, (Interaction.card_id == Card.id) & (Interaction.kind == "view")
              & (Interaction.user_id == user_id))
        .where(Card.series_id.isnot(None))
        .group_by(Card.series_id)
    ).all()
    done = []
    for series_id, seen_count in seen:
        total = session.execute(
            select(func.count(Card.id)).where(Card.series_id == series_id)
        ).scalar_one()
        if total and seen_count >= total:
            card = session.execute(
                select(Card).where(Card.series_id == series_id).limit(1)
            ).scalar_one_or_none()
            if card and card.series:
                done.append(card.series.name)
    return done


def profile(session: Session, user_id: str) -> dict:
    views = session.execute(
        select(func.count(Interaction.id)).where(
            Interaction.user_id == user_id, Interaction.kind == "view"
        )
    ).scalar_one()
    dwell = session.execute(
        select(func.coalesce(func.sum(Interaction.dwell_ms), 0)).where(
            Interaction.user_id == user_id, Interaction.kind == "view"
        )
    ).scalar_one()
    favorites = session.execute(
        select(func.count(Interaction.id)).where(
            Interaction.user_id == user_id, Interaction.kind == "favorite"
        )
    ).scalar_one()

    return {
        "user_id": user_id,
        "streak": current_streak(session, user_id),
        "level": _level(views),
        "stats": {
            "cards_viewed": views,
            "learning_minutes": round(dwell / 1000 / 60, 1),
            "favorites": favorites,
            "series_completed": completed_series(session, user_id),
        },
    }
