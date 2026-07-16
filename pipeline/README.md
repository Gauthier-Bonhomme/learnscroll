# LearnScroll — Pipeline de génération de contenu

Le feed ne lit **que** du contenu déjà généré et stocké en base. L'IA n'est
**jamais** appelée à l'ouverture d'une carte. Elle sert uniquement à remplir la
base, périodiquement, en lot. C'est ce qui rend l'app gratuite tenable.

```
fetch_news.py (RSS, sources réelles) ──► topics_news.json ─┐
topics_seed.json (evergreen) ──────────────────────────────┼─► generate_batch.py ──► [Message Batches API]
                                                           │            │
                                        poll_and_store.py ◄─────────────┘
                                                 │
                                                 ▼
                                     data/catalog.sqlite ──► export_site.py ──► site/data/*.json
                                                             (liens vérifiés)   (hébergement statique gratuit)
```

## Choix du modèle

Comme la génération est **hors ligne et sans contrainte de latence**, on passe
tout par la **Message Batches API** (−50 % sur input **et** output). Trois tiers,
sélectionnables par sujet ou globalement (`--tier`) :

| Tier | Modèle | Quand | Coût / carte* |
|------|--------|-------|---------------|
| `bulk` (défaut) | **Sonnet 5** | Le gros du catalogue. Qualité rédactionnelle quasi-Opus, coût très bas. | **0,0077 $** |
| `flagship` | **Opus 4.8** | Têtes de série, sujets phares, mode Actualité sensible. | 0,0194 $ |
| `hero` | **Fable 5** | Contenu héro, qualité maximale, usage rare. | 0,0387 $ |

\* Batches API (−50 %) + prompt caching du guide de style. Sonnet 5 au tarif
intro (2 $/10 $ par MTok jusqu'au 2026-08-31 ; posez `SONNET5_INTRO=0` ensuite).

**Pourquoi Sonnet 5 par défaut plutôt qu'Opus 4.8 ?** Le cahier des charges §10
fait de la minimisation des coûts une exigence produit explicite (« app
gratuite »). Sonnet 5 atteint une qualité proche d'Opus sur la rédaction
éditoriale pour ~2,5× moins cher. Le choix reste le vôtre : `--tier flagship`
bascule sur Opus 4.8, et chaque sujet peut fixer son propre tier.

### Coût du catalogue (mesuré via `estimate_cost.py`)

| Cartes | Sonnet 5 | Opus 4.8 | Fable 5 |
|-------:|---------:|---------:|--------:|
| 1 000 | 7,75 $ | 19,37 $ | 38,73 $ |
| 10 000 | 77,45 $ | 193,63 $ | 387,26 $ |
| 50 000 | 387,25 $ | 968,13 $ | 1 936,26 $ |

Un catalogue de **10 000 contenus riches coûte ~77 $** à générer. Le
réapprovisionnement périodique (nouvelles actus, nouvelles séries) se compte en
quelques dollars par semaine.

## Leviers de coût appliqués

- **Batches API** : −50 % sur tous les tokens. La génération n'a pas besoin
  d'être temps réel.
- **Prompt caching** : le guide de style (system, ~900 tokens) est identique
  pour toutes les cartes d'un lot → 1 écriture puis lectures à ~0,1×.
- **Structured Outputs** : sortie JSON stricte → stockage fiable, zéro token
  gaspillé en reformatage ou re-parsing.
- **Arbre « pourquoi » entièrement pré-généré** : 3-4 couches livrées dans la
  carte. Aucune génération au runtime → le site publié n'a besoin d'aucune clé
  API, d'aucun serveur, et n'expose aucun endpoint LLM abusable.
- **Idempotence** (`external_id` = `custom_id`) : relancer un lot ne regénère
  ni ne re-facture les cartes déjà en base.

## Utilisation

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...            # ou: ant auth login

python estimate_cost.py 10000           # chiffrer avant de lancer
python fetch_news.py                    # actus RSS -> sujets avec sources réelles
python generate_batch.py topics_news.json          # tier bulk (Sonnet 5)
python generate_batch.py topics_seed.json --tier flagship   # Opus 4.8
python poll_and_store.py                # attend la fin du lot puis stocke
python export_site.py                   # vérifie les liens, publie site/data/
```

Le batch se termine généralement en moins d'une heure (max 24 h). `poll_and_store.py`
interroge toutes les 30 s puis écrit les cartes au catalogue. Hors-ligne :
`python _selftest.py` valide tout le pipeline sans clé API.
