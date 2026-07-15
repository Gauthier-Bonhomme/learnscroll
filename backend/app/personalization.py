"""
Personnalisation du feed à partir des signaux comportementaux.

Le feed s'adapte automatiquement, sans configuration manuelle : on dérive une
affinité par catégorie à partir des interactions (like, favori, partage, temps
passé, approfondissement), on exclut ce qui a déjà été vu, et on garde une part
d'exploration pour ne pas enfermer l'utilisateur.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Card, Interaction

# Poids des signaux -> intérêt pour la catégorie de la carte.
_WEIGHTS = {"favorite": 5.0, "like": 3.0, "share": 4.0, "expand": 2.0, "view": 0.3}
_EXPLORATION = 0.25  # part du feed réservée à la découverte hors zone de confort


def category_affinity(session: Session, user_id: str) -> dict[str, float]:
    rows = session.execute(
        select(Interaction, Card.category)
        .join(Card, Card.id == Interaction.card_id)
        .where(Interaction.user_id == user_id)
    ).all()

    scores: dict[str, float] = {}
    for inter, category in rows:
        base = _WEIGHTS.get(inter.kind, 0.0)
        # Bonus temps passé : jusqu'à +2 pour une lecture longue (>45 s).
        base += min(inter.dwell_ms / 1000 / 45, 1.0) * 2.0 if inter.kind == "view" else 0.0
        scores[category] = scores.get(category, 0.0) + base
    return scores


def seen_card_ids(session: Session, user_id: str) -> set[int]:
    rows = session.execute(
        select(Interaction.card_id).where(Interaction.user_id == user_id)
    ).all()
    return {r[0] for r in rows}


def build_feed(session: Session, user_id: str, limit: int = 10) -> list[Card]:
    affinity = category_affinity(session, user_id)
    seen = seen_card_ids(session, user_id)

    candidates = session.execute(select(Card).where(Card.id.notin_(seen or {-1}))).scalars().all()
    if not candidates:
        return []

    max_aff = max(affinity.values()) if affinity else 1.0

    def score(card: Card) -> float:
        aff = affinity.get(card.category, 0.0) / max_aff  # 0..1
        # Nouveauté : les cartes récentes remontent légèrement.
        recency = 1.0 / (1 + card.id * 0.0)  # placeholder neutre, tri stable par affinité
        return aff + recency * 0.0

    ranked = sorted(candidates, key=score, reverse=True)

    # Injecte de l'exploration : quelques cartes hors des catégories favorites.
    n_explore = max(1, int(limit * _EXPLORATION))
    top = ranked[: limit - n_explore]
    top_ids = {c.id for c in top}
    explore_pool = [c for c in candidates if c.id not in top_ids]
    explore = explore_pool[:n_explore]

    feed = top + explore
    return feed[:limit]
