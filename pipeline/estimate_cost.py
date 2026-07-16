"""
Estimateur de coût de génération du catalogue LearnScroll.

Aucune dépendance externe : lance `python estimate_cost.py` (ou avec un volume :
`python estimate_cost.py 10000`). Modélise Batches API (-50 %) + prompt caching
sur le guide de style partagé.

Hypothèses par carte (schéma v2 : hook + teaser + body + 3-4 couches 'pourquoi'
+ sources + tags ; le champ image_prompt a été supprimé) :
  - guide de style (system, mis en cache)  ~950 tokens
  - prompt sujet (input non caché)          ~150 tokens (résumé RSS inclus)
  - sortie JSON structurée                 ~1500 tokens
"""

from __future__ import annotations

import sys

from config import TIERS

STYLE_GUIDE_TOKENS = 950     # system partagé -> cache après la 1re requête du lot
PROMPT_TOKENS = 150          # consigne sujet (+ résumé d'actu), unique par carte
OUTPUT_TOKENS = 1500         # carte JSON complète (4e couche 'pourquoi' incluse)

CACHE_WRITE_MULT = 1.25      # écriture cache (5 min)
CACHE_READ_MULT = 0.10       # lecture cache


def estimate(n_cards: int) -> None:
    print(f"\n=== Coût de génération pour {n_cards:,} cartes ===".replace(",", " "))
    print(f"{'Tier':<28}{'Modèle':<20}{'Total $':>12}{'$ / carte':>14}")
    print("-" * 74)

    for tier in TIERS.values():
        pin = tier.batch_price_in() / 1_000_000     # $ / token (batch)
        pout = tier.batch_price_out() / 1_000_000

        # Guide de style : 1 écriture cache, puis (n-1) lectures.
        style_cost = STYLE_GUIDE_TOKENS * pin * CACHE_WRITE_MULT
        style_cost += STYLE_GUIDE_TOKENS * pin * CACHE_READ_MULT * (n_cards - 1)

        # Prompts sujet + sorties : plein tarif batch.
        prompt_cost = PROMPT_TOKENS * pin * n_cards
        output_cost = OUTPUT_TOKENS * pout * n_cards

        total = style_cost + prompt_cost + output_cost
        print(f"{tier.label:<28}{tier.model_id:<20}{total:>12.2f}{total / n_cards:>14.4f}")

    print("-" * 74)
    print("Batches API : -50 % sur tous les tokens. Cache : guide de style partagé.")


if __name__ == "__main__":
    for n in ([int(sys.argv[1])] if len(sys.argv) > 1 else [1_000, 10_000, 50_000]):
        estimate(n)
