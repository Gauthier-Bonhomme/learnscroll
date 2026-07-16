"""
Interroge un batch jusqu'à complétion, parse les résultats et stocke les cartes
dans le catalogue (data/catalog.sqlite).

Usage :
    python poll_and_store.py               # utilise .last_batch
    python poll_and_store.py <batch_id>

Les résultats arrivent dans un ordre quelconque -> on retrouve chaque carte par
son custom_id. Le stockage est idempotent (external_id unique) : relancer ne
duplique rien. Les métadonnées de série et la source réelle viennent du mapping
.pending_topics.json écrit par generate_batch.py — pas de la sortie du modèle.
"""

from __future__ import annotations

import json
import os
import sys
import time

import anthropic

import catalog

_HERE = os.path.dirname(__file__)
_LAST = os.path.join(_HERE, ".last_batch")
_PENDING = os.path.join(_HERE, ".pending_topics.json")


def _resolve_batch_id() -> tuple[str, str]:
    if len(sys.argv) > 1:
        return sys.argv[1], ""
    if not os.path.exists(_LAST):
        sys.exit("Aucun batch_id fourni et .last_batch introuvable.")
    with open(_LAST, encoding="utf-8") as f:
        lines = f.read().splitlines()
    return lines[0], (lines[1] if len(lines) > 1 else "")


def _load_pending() -> dict[str, dict]:
    if not os.path.exists(_PENDING):
        return {}
    with open(_PENDING, encoding="utf-8") as f:
        return json.load(f)


def _wait(client: anthropic.Anthropic, batch_id: str) -> None:
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        if batch.processing_status == "ended":
            c = batch.request_counts
            print(f"✔ Terminé — succès={c.succeeded} erreurs={c.errored} expirés={c.expired}")
            return
        print(f"  … {batch.processing_status} (en cours : {batch.request_counts.processing})")
        time.sleep(30)


def _store(client: anthropic.Anthropic, batch_id: str, model_used: str) -> None:
    pending = _load_pending()
    conn = catalog.connect()
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
        topic = pending.get(cid, {})

        # La source réelle (RSS) prime sur ce que le modèle a cité.
        sources = data.get("sources", [])
        if topic.get("source"):
            src = topic["source"]
            sources = [{"title": src["title"], "url": src["url"]}]

        ok = catalog.upsert_card(conn, {
            "external_id": cid,
            "hook": data["hook"],
            "category": data["category"],
            "mode": data["mode"],
            "reading_time": data["reading_time"],
            "teaser": data["teaser"],
            "body": data["body"],
            "why_layers": data.get("why_layers", []),
            "sources": sources,
            "tags": data.get("tags", []),
            "series": topic.get("series", ""),
            "series_index": topic.get("series_index"),
            "series_total": topic.get("series_total"),
            "model_used": model_used or message.model,
        })
        if ok:
            stored += 1
            pending.pop(cid, None)
        else:
            skipped += 1

    conn.commit()
    conn.close()
    with open(_PENDING, "w", encoding="utf-8") as f:
        json.dump(pending, f, ensure_ascii=False, indent=1)
    print(f"→ Stockées : {stored} | déjà présentes : {skipped} | échecs : {failed}")
    print("  Puis :  python export_site.py")


def main() -> None:
    batch_id, model_used = _resolve_batch_id()
    client = anthropic.Anthropic()
    print(f"Batch : {batch_id}")
    _wait(client, batch_id)
    _store(client, batch_id, model_used)


if __name__ == "__main__":
    main()
