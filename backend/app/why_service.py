"""
Approfondissement récursif « J'ai compris… mais pourquoi ? ».

Les 2-3 premières couches sont pré-générées dans la carte (coût zéro au runtime).
Au-delà, on génère à la demande — mais une seule fois par (carte, question) :
la réponse est mise en cache et resservie ensuite. Coût borné, feed toujours
gratuit à parcourir.

Si aucune clé API n'est configurée, on renvoie une réponse dégradée propre
plutôt que de planter (le feed et les couches pré-générées restent intacts).
"""

from __future__ import annotations

import hashlib
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Card, WhyDeepCache

_MODEL = os.getenv("LEARNSCROLL_WHY_MODEL", "claude-sonnet-5")
_SYSTEM = (
    "Tu approfondis une explication pour l'app LearnScroll. On te donne un sujet, "
    "un contexte, et une question 'pourquoi'. Réponds en 2 à 4 phrases, en français, "
    "ton narratif et captivant, analogies si utile. Jamais de style Wikipédia. "
    "Termine en semant une nouvelle curiosité."
)


def _hash(question: str) -> str:
    return hashlib.sha256(question.strip().lower().encode("utf-8")).hexdigest()[:64]


def deepen(session: Session, card: Card, question: str) -> dict:
    qhash = _hash(question)
    cached = session.execute(
        select(WhyDeepCache).where(
            WhyDeepCache.card_id == card.id, WhyDeepCache.question_hash == qhash
        )
    ).scalar_one_or_none()
    if cached:
        return {"question": cached.question, "answer": cached.answer, "cached": True}

    answer = _generate(card, question)
    row = WhyDeepCache(card_id=card.id, question_hash=qhash, question=question, answer=answer)
    session.add(row)
    session.commit()
    return {"question": question, "answer": answer, "cached": False}


def _generate(card: Card, question: str) -> str:
    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
        return (
            "Cet approfondissement n'a pas encore été généré. "
            "(Configurez ANTHROPIC_API_KEY côté serveur pour l'activer.)"
        )
    try:
        import anthropic

        client = anthropic.Anthropic()
        context = f"Sujet : {card.hook}\nContexte : {card.teaser}\n{card.body[:600]}"
        resp = client.messages.create(
            model=_MODEL,
            max_tokens=400,
            thinking={"type": "disabled"},
            system=_SYSTEM,
            messages=[{"role": "user", "content": f"{context}\n\nQuestion : {question}"}],
        )
        return next((b.text for b in resp.content if b.type == "text"), "").strip()
    except Exception as exc:  # pragma: no cover - dégradation runtime
        return f"Approfondissement momentanément indisponible ({type(exc).__name__})."
