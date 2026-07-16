"""
Schéma d'une carte de connaissance LearnScroll.

On force la sortie du modèle via Structured Outputs (`output_config.format`) :
chaque carte revient en JSON strict, donc le stockage est fiable (pas de parsing
fragile). Les Structured Outputs ne supportent pas la récursion : l'arbre
« pourquoi ? » est pré-aplati en une liste de couches. Le site étant 100 %
statique, TOUTES les couches sont pré-générées (3 à 4) — rien n'est généré au
runtime.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CATEGORIES = [
    "science", "tech", "histoire", "geopolitique", "psychologie",
    "economie", "espace", "nature", "culture", "sante",
]

ReadingTime = Literal["30s", "2min", "5min"]


class WhyLayer(BaseModel):
    """Une couche de l'exploration récursive « J'ai compris… mais pourquoi ? »."""
    question: str = Field(..., description="La question 'pourquoi' de cette couche.")
    answer: str = Field(..., description="Réponse narrative, 2-4 phrases, jamais encyclopédique.")


class Source(BaseModel):
    title: str = Field(..., description="Nom de la source (NASA, CNRS, Inserm…).")
    url: str = Field(..., description="URL RÉELLE : soit la source fournie dans la consigne, soit la page d'accueil d'une institution connue. Jamais d'URL inventée.")


class KnowledgeCard(BaseModel):
    hook: str = Field(..., description="Titre accrocheur : question ou fait surprenant. Max ~90 caractères.")
    category: str = Field(..., description="Une des catégories LearnScroll.")
    mode: Literal["actualite", "info"] = Field(..., description="'actualite' (news reformulée) ou 'info' (evergreen).")
    reading_time: ReadingTime = Field(..., description="Temps de lecture estimé.")
    teaser: str = Field(..., description="1-2 phrases sous le titre, pour la carte du feed.")
    body: str = Field(..., description="Narration immersive du mode détail. Markdown léger autorisé. Commence par un hook fort, storytelling, analogies. INTERDIT : style Wikipedia.")
    why_layers: list[WhyLayer] = Field(..., description="3 à 4 couches de l'arbre 'pourquoi', chacune creusant la précédente.")
    sources: list[Source] = Field(..., description="1 à 3 sources fiables et RÉELLES.")
    tags: list[str] = Field(..., description="3 à 6 mots-clés.")


def card_json_schema() -> dict:
    """Schéma JSON pour `output_config.format` (contraint : additionalProperties=false, required complet)."""
    schema = KnowledgeCard.model_json_schema()
    _harden(schema)
    return schema


def _harden(node: dict) -> None:
    """Rend le schéma compatible Structured Outputs : additionalProperties=false + required = toutes les clés."""
    if node.get("type") == "object" and "properties" in node:
        node["additionalProperties"] = False
        node["required"] = list(node["properties"].keys())
        for prop in node["properties"].values():
            _harden(prop)
    for key in ("items", "$defs", "definitions"):
        sub = node.get(key)
        if isinstance(sub, dict):
            if key in ("$defs", "definitions"):
                for d in sub.values():
                    _harden(d)
            else:
                _harden(sub)
    for combinator in ("anyOf", "allOf", "oneOf"):
        for sub in node.get(combinator, []):
            _harden(sub)
