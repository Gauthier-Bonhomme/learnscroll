# LearnScroll — Pipeline de génération de contenu

Le feed ne lit **que** du contenu déjà généré et stocké en base. L'IA n'est
**jamais** appelée à l'ouverture d'une carte. Elle sert uniquement à remplir la
base, périodiquement, en lot. C'est ce qui rend l'app gratuite tenable.

```
topics_seed.json ──► generate_batch.py ──► [Message Batches API]
                                                    │
                     poll_and_store.py ◄────────────┘
                              │
                              ▼
                     learnscroll.db  ◄── le feed lit ici (aucun appel IA)
```

## Choix du modèle

Comme la génération est **hors ligne et sans contrainte de latence**, on passe
tout par la **Message Batches API** (−50 % sur input **et** output). Trois tiers,
sélectionnables par sujet ou globalement (`--tier`) :

| Tier | Modèle | Quand | Coût / carte* |
|------|--------|-------|---------------|
| `bulk` (défaut) | **Sonnet 5** | Le gros du catalogue. Qualité rédactionnelle quasi-Opus, coût très bas. | **0,0072 $** |
| `flagship` | **Opus 4.8** | Têtes de série, sujets phares, mode Actualité sensible. | 0,0180 $ |
| `hero` | **Fable 5** | Contenu héro, qualité maximale, usage rare. | 0,0361 $ |

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
| 1 000 | 7,21 $ | 18,03 $ | 36,06 $ |
| 10 000 | 72,10 $ | 180,25 $ | 360,51 $ |
| 50 000 | 360,50 $ | 901,25 $ | 1 802,51 $ |

Un catalogue de **10 000 contenus riches coûte ~72 $** à générer. Le
réapprovisionnement périodique (nouvelles actus, nouvelles séries) se compte en
quelques dollars par semaine.

## Leviers de coût appliqués

- **Batches API** : −50 % sur tous les tokens. La génération n'a pas besoin
  d'être temps réel.
- **Prompt caching** : le guide de style (system, ~900 tokens) est identique
  pour toutes les cartes d'un lot → 1 écriture puis lectures à ~0,1×.
- **Structured Outputs** : sortie JSON stricte → stockage fiable, zéro token
  gaspillé en reformatage ou re-parsing.
- **Arbre « pourquoi » pré-généré** : 2-3 couches livrées dans la carte. Les
  niveaux plus profonds sont générés à la demande **et mis en cache** (rare →
  coût borné), jamais régénérés.
- **Idempotence** (`external_id` = `custom_id`) : relancer un lot ne regénère
  ni ne re-facture les cartes déjà en base.

## Utilisation

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...            # ou: ant auth login

python estimate_cost.py 10000           # chiffrer avant de lancer
python generate_batch.py topics_seed.json          # tier bulk (Sonnet 5)
python generate_batch.py topics_seed.json --tier flagship   # Opus 4.8
python poll_and_store.py                # attend la fin du lot puis stocke
```

Le batch se termine généralement en moins d'une heure (max 24 h). `poll_and_store.py`
interroge toutes les 30 s puis écrit les cartes en base.
