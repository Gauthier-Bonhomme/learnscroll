"""Validation hors-ligne : schéma structuré + insertion/lecture en base. Sans API."""
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from content_schema import KnowledgeCard, card_json_schema
from app.db import Card, SessionLocal, init_db

# 1) Le schéma JSON est bien durci (additionalProperties=false + required complet)
schema = card_json_schema()
assert schema["additionalProperties"] is False
assert set(schema["required"]) == set(schema["properties"].keys())
defs = schema.get("$defs", {})
assert defs["WhyLayer"]["additionalProperties"] is False
print("✔ Schéma structuré durci :", len(schema["properties"]), "champs,", len(defs), "sous-types")

# 2) Une carte type valide bien contre Pydantic
sample = {
    "hook": "Pourquoi le ciel devient rouge au coucher du soleil ?",
    "category": "science", "mode": "info", "reading_time": "30s",
    "teaser": "Un simple filtre de lumière qui raconte 150 millions de km de voyage.",
    "body": "La lumière du soleil traverse plus d'air le soir...",
    "why_layers": [{"question": "Pourquoi plus d'air le soir ?",
                    "answer": "Le soleil est bas : ses rayons rasent l'atmosphère."}],
    "sources": [{"title": "NASA", "url": "https://science.nasa.gov"}],
    "image_prompt": "editorial photo of a red sunset, natural light",
    "tags": ["lumière", "atmosphère", "optique"],
}
card_model = KnowledgeCard.model_validate(sample)
print("✔ Carte validée par Pydantic :", card_model.hook[:40], "…")

# 3) Insertion + relecture en base
init_db()
s = SessionLocal()
s.query(Card).filter_by(external_id="selftest-1").delete()
c = Card(external_id="selftest-1", hook=sample["hook"], category="science",
         mode="info", reading_time="30s", teaser=sample["teaser"],
         body=sample["body"], image_prompt=sample["image_prompt"], model_used="selftest")
c.why_layers = sample["why_layers"]; c.sources = sample["sources"]; c.tags = sample["tags"]
s.add(c); s.commit()
back = s.query(Card).filter_by(external_id="selftest-1").one()
assert back.tags == ["lumière", "atmosphère", "optique"]
assert back.why_layers[0]["question"].startswith("Pourquoi")
print("✔ Aller-retour base OK — feed:", json.dumps(back.to_feed(), ensure_ascii=False)[:80], "…")
s.query(Card).filter_by(external_id="selftest-1").delete(); s.commit(); s.close()
print("\nTout est vert : le pipeline est sain hors-ligne.")
