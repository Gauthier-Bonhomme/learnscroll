"""
Configuration centrale du pipeline de génération de contenu LearnScroll.

Choix de modèle : le contenu est généré EN AMONT (batch), stocké en base, et le
feed ne lit que du contenu déjà généré. La génération n'est donc PAS sensible à
la latence -> on utilise systématiquement la Message Batches API (-50 % sur tous
les tokens) et le prompt caching sur le guide de style partagé.

Trois « tiers » de modèle sont disponibles. Par défaut on génère le gros du
catalogue avec Sonnet 5 (qualité quasi-Opus sur la rédaction, coût bien plus
faible) — justifié par l'exigence produit explicite « app gratuite / minimiser
les coûts d'API » (cahier des charges §10). Les contenus « piliers » (têtes de
série, sujets phares) peuvent être montés en gamme sur Opus 4.8, et Fable 5 est
disponible si on veut la qualité maximale sur du contenu héro.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


# --------------------------------------------------------------------------- #
# Tarifs publics ($ / million de tokens), cache API skill claude-api 2026-06.  #
# La Batches API applique -50 % sur input ET output.                           #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ModelTier:
    key: str
    model_id: str
    price_in: float          # $ / 1M tokens input (tarif standard hors batch)
    price_out: float         # $ / 1M tokens output (tarif standard hors batch)
    thinking: str            # "disabled" | "adaptive"
    label: str

    def batch_price_in(self) -> float:
        return self.price_in * 0.5

    def batch_price_out(self) -> float:
        return self.price_out * 0.5


# Sonnet 5 : tarif intro $2/$10 par MTok jusqu'au 2026-08-31, puis $3/$15.
# On code le tarif intro ; passe `SONNET5_INTRO=0` en env après l'échéance.
_SONNET5_INTRO = os.getenv("SONNET5_INTRO", "1") == "1"

TIERS: dict[str, ModelTier] = {
    "bulk": ModelTier(
        key="bulk",
        model_id="claude-sonnet-5",
        price_in=2.0 if _SONNET5_INTRO else 3.0,
        price_out=10.0 if _SONNET5_INTRO else 15.0,
        thinking="disabled",   # coût prévisible en volume
        label="Sonnet 5 (catalogue de masse)",
    ),
    "flagship": ModelTier(
        key="flagship",
        model_id="claude-opus-4-8",
        price_in=5.0,
        price_out=25.0,
        thinking="adaptive",   # têtes de série, sujets phares
        label="Opus 4.8 (contenu pilier)",
    ),
    "hero": ModelTier(
        key="hero",
        model_id="claude-fable-5",
        price_in=10.0,
        price_out=50.0,
        thinking="adaptive",   # qualité maximale, usage rare
        label="Fable 5 (contenu héro)",
    ),
}

# Tier utilisé par défaut si un sujet n'en spécifie pas.
DEFAULT_TIER = os.getenv("LEARNSCROLL_TIER", "bulk")

# Emplacement de la base partagée pipeline <-> backend.
DB_PATH = os.getenv(
    "LEARNSCROLL_DB",
    os.path.join(os.path.dirname(__file__), "..", "backend", "data", "learnscroll.db"),
)


def get_tier(name: str | None) -> ModelTier:
    return TIERS[name or DEFAULT_TIER]
