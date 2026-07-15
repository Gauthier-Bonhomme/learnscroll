"""
Interroge un batch jusqu'à complétion, parse les résultats et stocke les cartes.

Usage :
    python poll_and_store.py               # utilise .last_batch
    python poll_and_store.py <batch_id>

Les résultats arrivent dans un ordre quelconque -> on retrouve chaque carte par
son custom_id. Le stockage est idempotent (external_id unique) : relancer ne
duplique rien.
"""

from __future__ import annotations

import json
import os
import sys
import time

import anthropic

# Rend importable backend/app/db.py depuis le pipeline.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.db import Card, Series, SessionLocal, init_db  # noqa: E402

_LAST = os.path.join(os.path.dirname(__file__), ".last_batch")


def _resolve_batch_id() -> tuple[str, str]:
    if len(sys.argv) > 1:
        return sys.argv[1], ""
    if not os.path.exists(_LAST):
        sys.exit("Aucun batch_id fourni et .last_batch introuvable.")
    with open(_LAST, encoding="utf-8") as f:
        lines = f.read().splitlines()
    return lines[0], (lines[1] if len(lines) > 1 else "")


def _wait(client: anthropic.Anthropic, batch_id: str) -> None:
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        if batch.processing_status == "ended":
            c = batch.request_counts
            print(f"✔ Terminé — succès={c.succeeded} erreurs={c.errored} expirés={c.expired}")
            return
        print(f"  … {batch.processing_status} (en cours : {batch.request_counts.processing})")
        time.sleep(30)


def _get_or_create_series(session, name: str, category: str) -> Series | None:
    if not name:
        return None
    series = session.query(Series).filter_by(name=name).one_or_none()
    if series is None:
        series = Series(name=name, category=category or "")
        session.add(series)
        session.flush()
    return series


def _store(client: anthropic.Anthropic, batch_id: str, model_used: str) -> None:
    init_db()
    session = SessionLocal()
    stored = skipped = failed = 0

    for result in client.messages.batches.results(batch_id):
        cid = result.custom_id
        if result.result.type != "succeeded":
            failed += 1
            print(f"  ✗ {cid} : {result.result.type}")
            continue

        message = result.result.message
        text = next((b.text for b in message.content if b.type == "text"), None)
        if not text:
            failed += 1
            continue
        data = json.loads(text)

        if session.query(Card).filter_by(external_id=cid).first():
            skipped += 1
            continue

        series = _get_or_create_series(session, data.get("series", ""), data.get("category", ""))
        card = Card(
            external_id=cid,
            hook=data["hook"],
            category=data["category"],
            mode=data["mode"],
            reading_time=data["reading_time"],
            teaser=data["teaser"],
            body=data["body"],
            image_prompt=data.get("image_prompt", ""),
            model_used=model_used or message.model,
            series=series,
        )
        card.why_layers = data.get("why_layers", [])
        card.sources = data.get("sources", [])
        card.tags = data.get("tags", [])
        session.add(card)
        stored += 1

    session.commit()
    session.close()
    print(f"→ Stockées : {stored} | déjà présentes : {skipped} | échecs : {failed}")


def main() -> None:
    batch_id, model_used = _resolve_batch_id()
    client = anthropic.Anthropic()
    print(f"Batch : {batch_id}")
    _wait(client, batch_id)
    _store(client, batch_id, model_used)


if __name__ == "__main__":
    main()
