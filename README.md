# LearnScroll

> Remplacer le doomscrolling par du **learnscrolling** : un feed vertical type
> TikTok où chaque swipe fait apprendre quelque chose en moins de 60 secondes.

## Principe de coût (le cœur du modèle)

L'IA **n'est jamais** appelée à l'ouverture d'une carte. Tout le contenu est
généré **en amont, en lot**, stocké en base, et le feed ne lit que du contenu
déjà généré. L'IA sert uniquement à remplir et enrichir la base, périodiquement.

```
  pipeline/ (batch)                 backend/ (FastAPI)              mobile/ (Flutter)
 ┌──────────────────┐   écrit     ┌────────────────────┐   HTTP   ┌──────────────────┐
 │ Message Batches  │────────────▶│  learnscroll.db     │◀────────│  Feed vertical    │
 │ Sonnet 5 (-50%)  │             │  /api/feed …        │         │  Détail + pourquoi│
 │ + prompt caching │             │  + admin + webapp   │         │  Favoris + profil │
 └──────────────────┘             └────────────────────┘         └──────────────────┘
        aucun appel IA au runtime ───────────────┘
```

## Les trois briques

| Dossier | Rôle | Techno | État |
|---------|------|--------|------|
| `pipeline/` | Génération batch du contenu | Python + Anthropic SDK (Message Batches) | ✅ construit, testé hors-ligne |
| `backend/` | API du feed + admin CMS + app web de démo | FastAPI + SQLAlchemy (SQLite→PostgreSQL) | ✅ construit, endpoints vérifiés en direct |
| `mobile/` | App mobile de production | Flutter | ✅ écrit (nécessite le SDK Flutter pour compiler) |

## Démarrage

### 1. Backend + contenu de démo (aucune clé API requise)

```bash
cd backend
pip install -r requirements.txt
python seed_samples.py                       # insère 5 cartes de démo
python -m uvicorn app.main:app --port 8077
```

- Feed API : http://localhost:8077/api/feed
- App web (prototype du feed) : http://localhost:8077/app
- Admin CMS : http://localhost:8077/admin
- Docs OpenAPI : http://localhost:8077/docs

### 2. Générer du vrai contenu (batch)

```bash
cd pipeline
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...                  # ou: ant auth login
python estimate_cost.py 10000                 # chiffrer avant de lancer
python generate_batch.py topics_seed.json     # crée le job Batches (Sonnet 5)
python poll_and_store.py                       # attend la fin puis stocke en base
```

Coût : **~0,0072 $/carte** en Sonnet 5 batch (voir `pipeline/README.md` pour le
détail du choix de modèle et le tableau de coûts).

### 3. App mobile Flutter

```bash
cd mobile
flutter pub get
flutter run                                    # émulateur -> API sur 10.0.2.2:8077
# ou pointer un vrai serveur :
flutter run --dart-define=API_BASE=http://192.168.x.x:8077
```

## Ce qui est couvert (cahier des charges)

- **Feed vertical + cartes** (accroche, temps de lecture, ❤️/📤/👇) — feed & mobile
- **Mode détail narratif** + **arbre récursif « J'ai compris… mais pourquoi ? »**
- **Modes Actualité / Info** (champ `mode` sur chaque carte)
- **Personnalisation** automatique par affinité de catégorie (signaux : vues,
  temps passé, likes, favoris) + part d'exploration
- **Gamification** : streak journalier, niveaux (Curieux→Sage), stats, séries
- **Social** : favoris, partage, « Tu aimeras aussi », historique via interactions
- **CMS interne** pour préparer les sujets à générer
- **Pipeline IA batch** avec stockage — coûts minimisés

## Reste à faire

- Génération/sélection d'images éditoriales (le champ `image_prompt` est prêt ;
  brancher un générateur ou une banque d'images cohérente).
- Auth utilisateur (aujourd'hui : id local anonyme).
- Ordonnancement du réapprovisionnement (cron : nouvelles actus / séries).
