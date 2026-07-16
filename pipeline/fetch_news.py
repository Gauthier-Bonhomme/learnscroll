"""
Ingestion RSS -> sujets « actualité » avec sources RÉELLES.

Corrige le défaut le plus grave de la v1 (sources fabriquées par le modèle) :
chaque sujet d'actualité embarque désormais le titre et l'URL authentiques de
l'article source, qui seront cités tels quels dans la carte générée.

Zéro dépendance : parsing RSS 2.0 / Atom via xml.etree (stdlib).

Usage :
    python fetch_news.py                    # écrit topics_news.json
    python fetch_news.py --limit 3          # max 3 sujets par flux
    puis : python generate_batch.py topics_news.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET

import catalog

# Flux français de qualité, gratuits, stables. Le nom d'éditeur sert de titre
# de secours si l'item n'a pas de titre exploitable.
FEEDS = [
    ("franceinfo", "https://www.francetvinfo.fr/titres.rss"),
    ("Le Monde", "https://www.lemonde.fr/rss/une.xml"),
    ("The Conversation France", "https://theconversation.com/fr/articles.atom"),
    ("Sciences et Avenir", "https://www.sciencesetavenir.fr/rss.xml"),
]

_UA = {"User-Agent": "Mozilla/5.0 (LearnScroll pipeline; contact: admin@learnscroll.app)"}
_ATOM = "{http://www.w3.org/2005/Atom}"


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:400]


def _parse(data: bytes) -> list[dict]:
    """Extrait [{title, link, summary}] d'un flux RSS 2.0 ou Atom."""
    root = ET.fromstring(data)
    items = []

    for item in root.iter("item"):                      # RSS 2.0
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        summary = _strip_html(item.findtext("description") or "")
        if title and link:
            items.append({"title": title, "link": link, "summary": summary})

    for entry in root.iter(f"{_ATOM}entry"):            # Atom
        title = (entry.findtext(f"{_ATOM}title") or "").strip()
        link = ""
        for l in entry.findall(f"{_ATOM}link"):
            if l.get("rel") in (None, "alternate"):
                link = l.get("href", "")
                break
        summary = _strip_html(entry.findtext(f"{_ATOM}summary")
                              or entry.findtext(f"{_ATOM}content") or "")
        if title and link:
            items.append({"title": title, "link": link, "summary": summary})

    return items


def _topic_id(url: str) -> str:
    return "actu-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=5, help="Sujets max par flux.")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "topics_news.json"))
    args = ap.parse_args()

    conn = catalog.connect()
    topics: list[dict] = []

    for publisher, feed_url in FEEDS:
        try:
            items = _parse(_fetch(feed_url))
        except Exception as exc:
            print(f"  ✗ {publisher} : {type(exc).__name__} — flux ignoré")
            continue

        kept = 0
        for item in items:
            if kept >= args.limit:
                break
            if catalog.is_news_seen(conn, item["link"]):
                continue
            topics.append({
                "id": _topic_id(item["link"]),
                "title": item["title"],
                "mode": "actualite",
                "summary": item["summary"],
                "source": {"title": f"{publisher} — {item['title']}", "url": item["link"]},
            })
            catalog.mark_news_seen(conn, item["link"])
            kept += 1
        print(f"  ✔ {publisher} : {kept} nouveau(x) sujet(s)")

    conn.commit()
    conn.close()

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=1)
    print(f"→ {len(topics)} sujets écrits dans {os.path.basename(args.out)}")
    if topics:
        print("  Puis :  python generate_batch.py topics_news.json")


if __name__ == "__main__":
    main()
