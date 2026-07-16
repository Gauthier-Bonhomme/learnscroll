# LearnScroll

> Remplacer le doomscrolling par du **learnscrolling** : un feed vertical type
> TikTok où chaque swipe fait apprendre quelque chose en moins de 60 secondes.

## Le principe de coût (le cœur du modèle)

L'app est **gratuite pour toujours**, donc l'infrastructure doit tendre vers
**0 €** : le contenu est généré **en amont, en lot** (Batches API, −50 %),
stocké dans un catalogue, puis **exporté en fichiers statiques**. Le site
publié n'a **aucun serveur** : pas d'API, pas de base en production, pas
d'appel IA au runtime — donc pas de facture qui grimpe avec l'audience, et
aucune surface d'abus (pas d'endpoint LLM ouvert).

```
 pipeline/ (batch, ~0,008 $/carte)      data/catalog.sqlite       site/ (PWA statique)
┌───────────────────────────────┐      ┌────────────────┐      ┌─────────────────────────┐
│ fetch_news.py   (RSS réels)   │─────▶│  le catalogue   │─────▶│ data/index.json          │
│ generate_batch  (Sonnet 5)    │      │  s'accumule     │export│ data/cards/{id}.json     │
│ poll_and_store  (idempotent)  │      └────────────────┘      │ GitHub Pages / Cloudflare │
└───────────────────────────────┘                               └─────────────────────────┘
                                                                personnalisation, streaks,
                                                                favoris : 100 % sur l'appareil
```

La personnalisation, la gamification (streak en fuseau local, niveaux
Curieux→Sage), les favoris et l'historique vivent **dans le navigateur**
(localStorage) : vie privée par design, aucune donnée ne quitte l'appareil,
et l'app fonctionne hors-ligne (service worker).

## Démarrage (aucune clé API requise)

```bash
cd pipeline
python seed_samples.py        # 5 cartes de démo dans le catalogue
python export_site.py         # exporte les JSON statiques dans site/data/
python -m http.server 8077 --directory ../site
# → http://localhost:8077
```

## Générer du vrai contenu (batch)

```bash
cd pipeline
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...

python estimate_cost.py 10000            # chiffrer avant de lancer
python fetch_news.py                     # actus RSS -> sujets avec sources RÉELLES
python generate_batch.py topics_news.json     # ou topics_seed.json (evergreen)
python poll_and_store.py                 # attend la fin du lot, stocke au catalogue
python export_site.py                    # vérifie les liens + publie dans site/data/
```

Coût : **~0,008 $/carte** en Sonnet 5 batch (voir `pipeline/README.md`).
Réapprovisionner le feed = relancer ces quatre commandes (cron-able).

## Intégrité des sources

- Mode **actualité** : chaque sujet vient d'un flux RSS (franceinfo, Le Monde,
  The Conversation, Sciences et Avenir) et la carte cite **l'URL réelle de
  l'article source** — jamais une URL générée par le modèle.
- Mode **info** (evergreen) : le modèle ne peut citer que des pages d'accueil
  d'institutions connues, et `export_site.py` **vérifie chaque lien** au
  build ; les liens morts sont écartés, une actu sans source n'est pas publiée.

## Déploiement

Pousser sur `main` : le workflow `.github/workflows/deploy.yml` publie `site/`
sur GitHub Pages (gratuit, CDN). N'importe quel hébergeur statique fait
l'affaire (Cloudflare Pages, Netlify…).

## Fonctionnalités

- **Feed vertical** personnalisé par affinité de catégorie (vues, temps passé,
  favoris, partages) + part d'exploration + variation quotidienne déterministe
- **Mode détail narratif** + arbre **« J'ai compris… mais pourquoi ? »** à
  révélation progressive (3-4 couches pré-générées)
- **Cartes liées** (« Continuer à creuser ») calculées au build : épisode
  suivant d'une série d'abord, puis proximité de catégorie et de tags
- **Gamification** : streak journalier (fuseau local), niveaux, minutes
  apprises, progression des séries
- **Favoris** (toggle réel), **partage** (Web Share API + permalien `#c/id`)
- **PWA** : installable, offline, ~0 dépendance (zéro framework, zéro tracker)

## Structure

| Dossier | Rôle |
|---------|------|
| `pipeline/` | Génération batch (Anthropic SDK), ingestion RSS, export statique |
| `data/` | `catalog.sqlite` — le catalogue accumulé (l'actif du projet) |
| `site/` | La PWA publiée : HTML/CSS/JS vanilla + `data/` exporté |
