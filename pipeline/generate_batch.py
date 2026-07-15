"""
Crée un job Message Batches pour générer un lot de cartes LearnScroll.

Usage :
    python generate_batch.py topics_seed.json
    python generate_batch.py topics_seed.json --tier flagship

Écrit l'ID du batch dans .last_batch pour poll_and_store.py.

Pourquoi Batches API : la génération est faite en amont, hors ligne, sans
contrainte de latence -> -50 % sur tous les tokens. Le guide de style (system)
est mis en cache : identique pour toutes les requêtes du lot.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

from config import get_tier
from content_schema import card_json_schema
from prompts import STYLE_GUIDE, user_prompt

_SCHEMA = card_json_schema()
_LAST = os.path.join(os.path.dirname(__file__), ".last_batch")


def _params(topic: dict, tier) -> MessageCreateParamsNonStreaming:
    params: MessageCreateParamsNonStreaming = {
        "model": tier.model_id,
        "max_tokens": 4096,
        "system": [
            {
                "type": "text",
                "text": STYLE_GUIDE,
                "cache_control": {"type": "ephemeral"},  # guide partagé -> cache
            }
        ],
        "output_config": {"format": {"type": "json_schema", "schema": _SCHEMA}},
        "messages": [{"role": "user", "content": user_prompt(topic)}],
    }
    # Sonnet 5 : adaptive par défaut. On désactive pour un coût prévisible en
    # volume (tier "bulk"). Les tiers premium gardent l'adaptive.
    if tier.thinking == "disabled":
        params["thinking"] = {"type": "disabled"}
    else:
        params["thinking"] = {"type": "adaptive"}
    return params


def build_requests(topics: list[dict], tier) -> list[Request]:
    reqs: list[Request] = []
    for i, topic in enumerate(topics):
        # custom_id stable = idempotence côté stockage.
        cid = topic.get("id") or f"{tier.key}-{i:05d}-{_slug(topic['title'])}"
        reqs.append(Request(custom_id=cid, params=_params(topic, tier)))
    return reqs


def _slug(s: str) -> str:
    keep = "".join(c if c.isalnum() else "-" for c in s.lower())
    return "-".join(filter(None, keep.split("-")))[:40]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("topics", help="Fichier JSON : liste de sujets.")
    ap.add_argument("--tier", default=None, help="bulk | flagship | hero")
    args = ap.parse_args()

    tier = get_tier(args.tier)
    with open(args.topics, encoding="utf-8") as f:
        topics = json.load(f)

    requests = build_requests(topics, tier)
    print(f"→ {len(requests)} cartes à générer avec {tier.label} ({tier.model_id})")

    client = anthropic.Anthropic()
    batch = client.messages.batches.create(requests=requests)
    with open(_LAST, "w", encoding="utf-8") as f:
        f.write(f"{batch.id}\n{tier.model_id}\n")

    print(f"✔ Batch créé : {batch.id}  (statut : {batch.processing_status})")
    print("  Puis :  python poll_and_store.py")


if __name__ == "__main__":
    sys.exit(main())
