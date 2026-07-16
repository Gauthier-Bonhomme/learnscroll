"""
Auto-test hors-ligne du pipeline (aucune clé API, aucun réseau).

    python _selftest.py

Couvre : durcissement du schéma Structured Outputs, prompts (source réelle),
aller-retour catalogue sqlite3, export statique complet (index + détails +
cartes liées), et exclusion d'une actu sans source.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

import catalog
import export_site
from content_schema import CATEGORIES, KnowledgeCard, card_json_schema
from prompts import user_prompt

FAILURES: list[str] = []


def check(label: str, ok: bool) -> None:
    print(f"  {'✔' if ok else '✗'} {label}")
    if not ok:
        FAILURES.append(label)


def _walk_objects(node):
    if isinstance(node, dict):
        if node.get("type") == "object" and "properties" in node:
            yield node
        for v in node.values():
            yield from _walk_objects(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_objects(v)


def test_schema() -> None:
    print("\n[1] Schéma Structured Outputs")
    schema = card_json_schema()
    objs = list(_walk_objects(schema))
    check("au moins un objet dans le schéma", len(objs) >= 2)
    check("additionalProperties=false partout",
          all(o.get("additionalProperties") is False for o in objs))
    check("required = toutes les clés partout",
          all(set(o.get("required", [])) == set(o["properties"].keys()) for o in objs))
    check("image_prompt supprimé du schéma",
          "image_prompt" not in schema.get("properties", {}))

    card = KnowledgeCard(
        hook="Test ?", category="science", mode="info", reading_time="30s",
        teaser="t", body="b",
        why_layers=[{"question": "q", "answer": "a"}],
        sources=[{"title": "NASA", "url": "https://www.nasa.gov"}],
        tags=["a", "b", "c"],
    )
    check("validation Pydantic d'une carte", card.category in CATEGORIES)


def test_prompts() -> None:
    print("\n[2] Prompts")
    p = user_prompt({
        "title": "Sujet", "mode": "actualite", "summary": "Résumé de l'actu.",
        "source": {"title": "franceinfo — Titre", "url": "https://example.org/a"},
    })
    check("la source réelle figure dans la consigne", "https://example.org/a" in p)
    check("le résumé figure dans la consigne", "Résumé de l'actu." in p)
    p2 = user_prompt({"title": "S", "series": "Les Romains", "series_index": 2, "series_total": 12})
    check("les métadonnées de série figurent dans la consigne", "épisode 2/12" in p2)


def _demo_card(eid: str, **over) -> dict:
    base = dict(
        external_id=eid, hook=f"Hook {eid} ?", category="science", mode="info",
        reading_time="30s", teaser="Teaser.", body="Corps du texte.",
        why_layers=[{"question": "q", "answer": "a"}],
        sources=[{"title": "NASA", "url": "https://www.nasa.gov"}],
        tags=["alpha", "beta"],
    )
    base.update(over)
    return base


def _id_by_hook(index: dict, eid: str) -> int:
    return next(c["id"] for c in index["cards"] if c["hook"] == f"Hook {eid} ?")


def test_catalog_and_export() -> None:
    print("\n[3] Catalogue + export statique")
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "cat.sqlite")
        conn = catalog.connect(db)
        check("insertion", catalog.upsert_card(conn, _demo_card("a1")))
        check("idempotence (même external_id ignoré)",
              not catalog.upsert_card(conn, _demo_card("a1")))
        catalog.upsert_card(conn, _demo_card(
            "a2", category="histoire", series="Les Romains", series_index=1,
            series_total=12, tags=["rome"]))
        catalog.upsert_card(conn, _demo_card(
            "a3", category="histoire", series="Les Romains", series_index=2,
            series_total=12, tags=["rome"]))
        # Actu sans source valide -> ne doit pas être publiée.
        catalog.upsert_card(conn, _demo_card("a4", mode="actualite", sources=[]))
        conn.commit()

        cards = catalog.all_cards(conn)
        check("aller-retour JSON (why_layers)", cards[0]["why_layers"][0]["question"] == "q")
        catalog.mark_news_seen(conn, "http://x")
        check("news_seen", catalog.is_news_seen(conn, "http://x"))
        conn.close()

        catalog.DB_PATH = db  # export_site lit le catalogue via ce chemin
        out = os.path.join(tmp, "data")
        report = export_site.export(out, linkcheck=False)

        with open(os.path.join(out, "index.json"), encoding="utf-8") as f:
            index = json.load(f)
        check("3 cartes publiées (l'actu sans source est exclue)",
              index["total"] == 3 and report["news_excluded_no_source"] == 1)
        check("série présente avec total déclaré",
              index["series"][0]["name"] == "Les Romains" and index["series"][0]["total"] == 12)
        check("feed trié du plus récent au plus ancien",
              [c["id"] for c in index["cards"]]
              == sorted((c["id"] for c in index["cards"]), reverse=True))

        ep1, ep2 = _id_by_hook(index, "a2"), _id_by_hook(index, "a3")
        with open(os.path.join(out, "cards", f"{ep1}.json"), encoding="utf-8") as f:
            detail = json.load(f)
        check("détail : body + why_layers + sources + related",
              all(k in detail for k in ("body", "why_layers", "sources", "related")))
        related_ids = [r["id"] for r in detail["related"]]
        check("l'épisode 2 est la 1re carte liée de l'épisode 1",
              bool(related_ids) and related_ids[0] == ep2)


def main() -> None:
    test_schema()
    test_prompts()
    test_catalog_and_export()
    print()
    if FAILURES:
        print(f"✗ {len(FAILURES)} échec(s) : {FAILURES}")
        sys.exit(1)
    print("✔ Tous les tests passent.")


if __name__ == "__main__":
    main()
