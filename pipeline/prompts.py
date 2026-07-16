"""
Guide de style éditorial LearnScroll (system prompt partagé) + prompts par sujet.

Le guide de style est IDENTIQUE pour toutes les cartes d'un batch -> on le place
en `system` avec `cache_control` : après la 1re requête, il est servi depuis le
cache (~0,1x le prix). Sur un batch de 1000 cartes, c'est ~999 lectures de cache
au lieu de 999 traitements plein tarif.

Règle d'or sur les sources : le modèle n'invente JAMAIS d'URL. En mode
actualité, la source réelle (titre + URL du flux RSS) est fournie dans la
consigne et doit être citée telle quelle. En mode info, seules des pages
d'accueil d'institutions connues sont autorisées — et export_site.py vérifie
chaque lien au build (les liens morts sont écartés).
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
- Inventer des faits. Si tu n'es pas sûr, reste général et vrai.
- Inventer des URLs. C'est la règle la plus stricte de toutes (voir SOURCES).

STRUCTURE
- hook : le titre. Une question ou un fait qui claque. ~90 caractères max.
- teaser : 1-2 phrases qui donnent envie d'ouvrir, sous le titre du feed.
- body : le mode détail. Ouvre par un hook puissant, déroule une explication \
progressive et captivante, termine sur une chute mémorable. Markdown léger OK.
- why_layers : 3 à 4 couches de « J'ai compris… mais pourquoi ? ». Chaque \
couche creuse la précédente d'un cran, comme un arbre de connaissance. La \
dernière couche peut ouvrir vers une question plus vaste (chute).
- tags : 3 à 6 mots-clés simples, en minuscules.

SOURCES (RÈGLE STRICTE — la confiance du lecteur en dépend)
- Si la consigne fournit une « Source réelle », cite-la EXACTEMENT (titre et \
URL tels quels), c'est ta source principale et obligatoire.
- Sinon, cite 1 à 3 institutions dont tu es certain, avec UNIQUEMENT l'URL de \
leur page d'accueil : https://www.nasa.gov, https://lejournal.cnrs.fr, \
https://www.inserm.fr, https://www.nature.com, https://www.ined.fr, \
https://www.reuters.com, https://www.bbc.com, https://www.esa.int…
- JAMAIS de chemin profond inventé (pas de /articles/2026/xyz fabriqué). \
Chaque lien est vérifié automatiquement : un lien mort discrédite la carte.

MODE ACTUALITÉ vs INFO
- mode="actualite" : reformule COMPLÈTEMENT l'actu fournie (jamais de copie, \
aucune phrase reprise), ajoute le contexte et le « pourquoi c'est important ».
- mode="info" : concept, phénomène, histoire evergreen. Objectif curiosité + \
culture générale.

Réponds UNIQUEMENT via le format structuré demandé.\
"""


def user_prompt(topic: dict) -> str:
    """Construit la consigne de génération pour un sujet.

    `topic` attend au minimum {"title": str}. Optionnels : "category", "mode",
    "reading_time", "series", "series_index", "series_total", "angle",
    "source" ({"title", "url"} — actu réelle issue du RSS, à citer telle quelle).
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
    if topic.get("summary"):
        lines.append(f"Résumé de l'actu (à reformuler complètement) : {topic['summary']}")
    if topic.get("source"):
        src = topic["source"]
        lines.append(
            f"Source réelle à citer EXACTEMENT (titre et URL tels quels) : "
            f"« {src['title']} » — {src['url']}"
        )
    if topic.get("series"):
        idx = topic.get("series_index", "?")
        total = topic.get("series_total", "?")
        lines.append(
            f"Cette carte fait partie de la série « {topic['series']} » "
            f"(épisode {idx}/{total}). Assure une continuité de ton avec la série "
            f"et une accroche qui fonctionne aussi de façon autonome."
        )

    lines.append(
        "Rappelle-toi : accroche forte d'abord, narration, zéro style Wikipédia, "
        "zéro URL inventée."
    )
    return "\n".join(lines)
