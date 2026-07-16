"""
Exporte le catalogue en JSON statiques pour le site (hébergement gratuit, CDN).

    catalog.sqlite ──► site/data/index.json          (feed : métadonnées légères)
                   ──► site/data/cards/{id}.json     (détail : body, pourquoi, sources, liées)

C'est la pièce qui remplace le backend : tout ce que FastAPI calculait au
runtime (recommandations, séries, stats) est calculé ICI, une fois, au build.

Intégrité des sources : chaque URL est vérifiée (HTTP < 400). Les liens morts
sont écartés ; une carte « actualité » sans source valide n'est pas publiée.
Les erreurs réseau (timeout, DNS) ne condamnent pas un lien : on garde et on
signale (pour ne pas vider le site lors d'un build hors-ligne).

Usage :
    python export_site.py
    python export_site.py --no-linkcheck      # build hors-ligne
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

import catalog
from content_schema import CATEGORIES

_DEFAULT_OUT = os.path.join(os.path.dirname(__file__), "..", "site", "data")
_UA = {"User-Agent": "Mozilla/5.0 (compatible; LearnScroll link checker)"}


# --------------------------------------------------------------------------- #
# Vérification des liens                                                      #
# --------------------------------------------------------------------------- #
def check_url(url: str) -> str:
    """'ok' | 'dead' | 'unknown'.

    Seule une page réellement disparue (404/410) condamne un lien : 403/429
    sont des réponses anti-bot de sites bien vivants (Reuters…), et une
    erreur réseau ne prouve rien — on garde et on signale.
    """
    if not url.startswith(("http://", "https://")):
        return "dead"
    req = urllib.request.Request(url, headers=_UA, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return "ok" if resp.status < 400 else "unknown"
    except urllib.error.HTTPError as exc:
        return "dead" if exc.code in (404, 410) else "unknown"
    except Exception:
        return "unknown"


def validate_sources(cards: list[dict], enabled: bool) -> dict:
    """Écarte les sources mortes (mutation en place). Renvoie le rapport."""
    report = {"checked": 0, "dropped": 0, "unknown": 0}
    if not enabled:
        return report
    cache: dict[str, str] = {}
    for card in cards:
        kept = []
        for src in card["sources"]:
            url = src.get("url", "")
            if url not in cache:
                cache[url] = check_url(url)
                report["checked"] += 1
            status = cache[url]
            if status == "dead":
                report["dropped"] += 1
                print(f"  ✗ lien mort écarté : {url}  (carte #{card['id']})")
            else:
                if status == "unknown":
                    report["unknown"] += 1
                kept.append(src)
        card["sources"] = kept
    return report


# --------------------------------------------------------------------------- #
# Cartes liées (remplace GET /api/recommendations)                            #
# --------------------------------------------------------------------------- #
def related_cards(card: dict, cards: list[dict], k: int = 4) -> list[dict]:
    def score(other: dict) -> float:
        s = 0.0
        if card["series"] and other["series"] == card["series"]:
            s += 10
            # L'épisode suivant d'abord.
            if (other.get("series_index") or 0) == (card.get("series_index") or 0) + 1:
                s += 5
        if other["category"] == card["category"]:
            s += 3
        tags = {t.lower() for t in card["tags"]}
        s += len(tags & {t.lower() for t in other["tags"]})
        return s

    ranked = sorted((c for c in cards if c["id"] != card["id"]), key=score, reverse=True)
    return [
        {"id": c["id"], "hook": c["hook"], "category": c["category"],
         "reading_time": c["reading_time"]}
        for c in ranked[:k] if score(c) > 0
    ]


# --------------------------------------------------------------------------- #
# Export                                                                      #
# --------------------------------------------------------------------------- #
def export(out_dir: str, linkcheck: bool = True) -> dict:
    conn = catalog.connect()
    cards = catalog.all_cards(conn)
    conn.close()

    # Garde-fou qualité : une carte incomplète ne sort pas.
    publishable = []
    for c in cards:
        if not (c["hook"] and c["teaser"] and c["body"]) or c["category"] not in CATEGORIES:
            print(f"  ! carte #{c['id']} incomplète ou catégorie inconnue — exclue")
            continue
        publishable.append(c)

    link_report = validate_sources(publishable, linkcheck)

    # Une actu sans source valide n'est pas publiable (confiance).
    final = [c for c in publishable
             if c["sources"] or c["mode"] != "actualite"]
    excluded_news = len(publishable) - len(final)

    # Séries : total = déclaré au sujet, sinon nombre de cartes présentes.
    series_map: dict[str, list[dict]] = {}
    for c in final:
        if c["series"]:
            series_map.setdefault(c["series"], []).append(c)
    series_out = []
    for name, members in sorted(series_map.items()):
        members.sort(key=lambda c: c.get("series_index") or 0)
        declared = max((c.get("series_total") or 0) for c in members)
        series_out.append({
            "name": name,
            "category": members[0]["category"],
            "total": max(declared, len(members)),
            "card_ids": [c["id"] for c in members],
        })

    cards_dir = os.path.join(out_dir, "cards")
    os.makedirs(cards_dir, exist_ok=True)
    for stale in glob.glob(os.path.join(cards_dir, "*.json")):
        os.remove(stale)

    feed_fields = ("id", "hook", "teaser", "category", "mode", "reading_time",
                   "tags", "series", "series_index", "created_at")
    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total": len(final),
        "categories": sorted({c["category"] for c in final}),
        "series": series_out,
        "cards": [{k: c[k] for k in feed_fields}
                  for c in sorted(final, key=lambda c: c["id"], reverse=True)],
    }
    with open(os.path.join(out_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))

    for c in final:
        detail = {k: c[k] for k in feed_fields}
        detail.update({
            "body": c["body"],
            "why_layers": c["why_layers"],
            "sources": c["sources"],
            "series_total": c.get("series_total"),
            "related": related_cards(c, final),
        })
        with open(os.path.join(cards_dir, f"{c['id']}.json"), "w", encoding="utf-8") as f:
            json.dump(detail, f, ensure_ascii=False, separators=(",", ":"))

    # Rapport (remplace l'admin de la v1).
    by_cat: dict[str, int] = {}
    no_sources = 0
    for c in final:
        by_cat[c["category"]] = by_cat.get(c["category"], 0) + 1
        no_sources += 0 if c["sources"] else 1
    report = {
        "published": len(final),
        "by_category": by_cat,
        "series": len(series_out),
        "links_checked": link_report["checked"],
        "links_dropped": link_report["dropped"],
        "links_unknown": link_report["unknown"],
        "news_excluded_no_source": excluded_news,
        "cards_without_sources": no_sources,
    }
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=_DEFAULT_OUT)
    ap.add_argument("--no-linkcheck", action="store_true",
                    help="Saute la vérification des liens (build hors-ligne).")
    args = ap.parse_args()

    report = export(os.path.abspath(args.out), linkcheck=not args.no_linkcheck)
    print("\n=== Export du site ===")
    for key, val in report.items():
        print(f"  {key:<28} {val}")
    print(f"  → {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
