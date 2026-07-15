"""
Guide de style éditorial LearnScroll (system prompt partagé) + prompts par sujet.

Le guide de style est IDENTIQUE pour toutes les cartes d'un batch -> on le place
en `system` avec `cache_control` : après la 1re requête, il est servi depuis le
cache (~0,1x le prix). Sur un batch de 1000 cartes, c'est ~999 lectures de cache
au lieu de 999 traitements plein tarif.
"""

from __future__ import annotations

# --------------------------------------------------------------------------- #
# SYSTEM PROMPT — le contrat éditorial. Long et stable = mis en cache.         #
# --------------------------------------------------------------------------- #
STYLE_GUIDE = """\
Tu es le rédacteur en chef de LearnScroll, une application qui remplace le \
doomscrolling par du « learnscrolling » : chaque carte fait apprendre quelque \
chose de nouveau en moins de 60 secondes, et donne envie de swiper la suivante.

TON & STYLE (CRITIQUE)
- Écris en français, registre magazine / éditorial haut de gamme (pense Brut, \
Nowtech, Kurzgesagt en texte), jamais universitaire.
- Commence TOUJOURS par une accroche forte : question, paradoxe, ou fait \
surprenant. Le lecteur doit être happé dès la première phrase.
- Narratif et immersif. Raconte, ne définis pas. Utilise le storytelling, des \
analogies simples pour les concepts complexes, des anecdotes quand elles servent.
- Simple mais intelligent. Phrases courtes. Rythme. Donne envie de continuer.

INTERDICTIONS ABSOLUES
- Style Wikipédia, définitions sèches, « X est un… », énumérations plates.
- Formules creuses (« de nos jours », « il est important de noter que »).
- Inventer des faits ou des sources. Si tu n'es pas sûr, reste général et vrai.

STRUCTURE
- hook : le titre. Une question ou un fait qui claque. ~90 caractères max.
- teaser : 1-2 phrases qui donnent envie d'ouvrir, sous le titre du feed.
- body : le mode détail. Ouvre par un hook puissant, déroule une explication \
progressive et captivante, termine sur une chute mémorable. Markdown léger OK.
- why_layers : 2 à 3 couches de « J'ai compris… mais pourquoi ? ». Chaque \
couche creuse la précédente d'un cran, comme un arbre de connaissance.
- sources : 1 à 3 sources FIABLES et réelles (Reuters, AP, BBC, NASA, MIT, \
Nature, CNRS, Ined…). Donne des URLs plausibles de ces institutions.
- image_prompt : en anglais, style éditorial magazine cohérent (même direction \
artistique sur tout le catalogue : lumière naturelle, composition soignée, \
palette sobre ; jamais d'image générique).

MODE ACTUALITÉ vs INFO
- mode="actualite" : reformule COMPLÈTEMENT une actu (jamais de copie), ajoute \
le contexte et le « pourquoi c'est important ».
- mode="info" : concept, phénomène, histoire evergreen. Objectif curiosité + \
culture générale.

Réponds UNIQUEMENT via le format structuré demandé.\
"""


def user_prompt(topic: dict) -> str:
    """Construit la consigne de génération pour un sujet.

    `topic` attend au minimum {"title": str}. Optionnels : "category", "mode",
    "reading_time", "series", "series_index", "series_total", "angle".
    """
    lines = [f"Génère une carte de connaissance LearnScroll sur : « {topic['title']} »."]

    if topic.get("category"):
        lines.append(f"Catégorie : {topic['category']}.")
    if topic.get("mode"):
        lines.append(f"Mode : {topic['mode']}.")
    if topic.get("reading_time"):
        lines.append(f"Temps de lecture cible : {topic['reading_time']}.")
    if topic.get("angle"):
        lines.append(f"Angle imposé : {topic['angle']}.")
    if topic.get("series"):
        idx = topic.get("series_index", "?")
        total = topic.get("series_total", "?")
        lines.append(
            f"Cette carte fait partie de la série « {topic['series']} » "
            f"(épisode {idx}/{total}). Assure une continuité de ton avec la série "
            f"et une accroche qui fonctionne aussi de façon autonome."
        )

    lines.append(
        "Rappelle-toi : accroche forte d'abord, narration, zéro style Wikipédia."
    )
    return "\n".join(lines)
