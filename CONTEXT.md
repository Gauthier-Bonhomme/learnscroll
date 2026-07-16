# LearnScroll — État du projet (16/07/2026, refonte v2)

App « TikTok de l'apprentissage » : remplacer le doomscrolling par du
learnscrolling. **Contrainte produit centrale : app gratuite pour toujours →
architecture 100 % statique, 0 € d'hébergement, aucun appel IA au runtime.**

## Refonte v2 (16/07/2026) — décisions actées

La v1 (FastAPI + SQLAlchemy + webapp servie + app Flutter jamais compilée) a
été **remplacée** par un site statique. Motifs : le endpoint `/why` ouvert
était une bombe à coûts (LLM sans auth ni quota), un serveur 24/7 coûte
5-20 €/mois pour du contenu 100 % pré-généré, les sources étaient fabriquées
par le modèle, Flutter était un poids mort (SDK absent, stores payants).
**Tout l'ancien code reste dans git** (commit initial `78f249b`).

## Emplacement & environnement

- Projet : `C:\Users\Gauthier\Desktop\learnscroll\` — dépôt git, remote
  `https://github.com/Gauthier-Bonhomme/learnscroll` (public, requis pour Pages gratuit).
- **Site en ligne : https://gauthierbonhomme.com/learnscroll/** (Pages en mode
  workflow ; le domaine du site CV s'applique aux project pages). Déployé le
  16/07/2026, vérifié 200 + index.json servi. Push sur `site/**` = redéploiement auto.
- Machine : Windows 11 ; Python 3.14 (lancer avec `-X utf8` pour les emojis console).
- Deps pip : anthropic, pydantic (rien d'autre ; SQLAlchemy/FastAPI plus utilisés).
- Preview : entrée `learnscroll-site` dans `mon-cv\images\.claude\launch.json`
  (c'est CE launch.json que lisent les preview tools des sessions CV) + copie
  locale dans `.claude/launch.json` du projet. Port 8077, `python -m http.server`.

## Architecture v2 (2 briques + 1 actif)

```
pipeline/ (batch IA + export) ──► data/catalog.sqlite ──► site/ (PWA statique, aucun serveur)
```

### 1. `pipeline/` — génération + export (TESTÉ : `_selftest.py` vert, RSS testé en réel)

- `catalog.py` : catalogue SQLite en **stdlib sqlite3** (plus de SQLAlchemy).
  Tables `cards` (série en colonne texte) + `news_seen` (dédup RSS). Idempotence par `external_id`.
- `config.py` : 3 tiers — bulk=Sonnet 5 (0,0077 $/carte batch), flagship=Opus 4.8
  (0,0194 $), hero=Fable 5 (0,0387 $). `SONNET5_INTRO=0` après le 2026-08-31.
- `content_schema.py` : `KnowledgeCard` sans `image_prompt` (supprimé), 3-4 why_layers.
- `prompts.py` : STYLE_GUIDE avec règle stricte anti-URL-inventée ; sources =
  soit la source RSS fournie (citée telle quelle), soit page d'accueil d'institution connue.
- `fetch_news.py` : **NOUVEAU** — RSS (franceinfo, Le Monde, The Conversation,
  Sciences et Avenir) → `topics_news.json` avec sources réelles. Stdlib xml.etree.
- `generate_batch.py` : écrit `.pending_topics.json` (mapping custom_id→sujet) —
  corrige le bug v1 où les séries n'étaient jamais rattachées depuis un batch.
- `poll_and_store.py` : stocke au catalogue ; la source RSS du sujet écrase les sources du modèle.
- `export_site.py` : **NOUVEAU** — catalogue → `site/data/index.json` +
  `site/data/cards/{id}.json` + cartes liées calculées au build + **vérification
  des liens** (mort = 404/410 seulement ; 403/429 = anti-bot, on garde) +
  rapport qualité. Une actu sans source valide n'est pas publiée.
- Jamais lancé contre l'API réelle (aucun batch payé à ce jour).

### 2. `site/` — PWA statique (VÉRIFIÉE en local via http.server + Browser pane)

- Vanilla HTML/CSS/JS, zéro framework, zéro tracker. DA conservée (Fraunces +
  Inter, fond #0C0B0A, accent ambre #E0A367, teinte par catégorie — bug v1
  corrigé : les variables CSS portent les noms exacts des slugs).
- **Tout côté client (localStorage)** : personnalisation (affinité catégorie +
  exploration + jitter quotidien déterministe + diversité anti-monotonie),
  gamification (streak en **fuseau local**, niveaux Curieux→Sage, minutes,
  progression séries), favoris (toggle réel), cartes vues exclues du feed.
- Détail : arbre « pourquoi » à **révélation progressive** (1 couche par clic),
  cartes liées « Continuer à creuser », sources cliquables. Échappement HTML
  systématique (XSS v1 corrigé). Permaliens `#c/id`. Web Share API.
- `sw.js` : offline (coquille cache-first, index network-first, cartes au fil de l'eau).
- `.github/workflows/deploy.yml` : push main → GitHub Pages (dossier `site/`).

## Vérifié le 16/07/2026

Selftest pipeline 100 % vert ; seed 5 cartes + export réel OK ; RSS réel : 8
sujets/4 flux avec vraies URLs ; dans le navigateur : feed rendu, détail,
pourquoi progressif, favoris, profil, permalien après reload, persistance,
exclusion des vues, 0 erreur console. Limites de l'environnement de test :
screenshots et IntersectionObserver inertes dans le Browser pane (renderer sans
frames) — le dwell tracking (pattern identique v1) est à re-vérifier sur un
vrai appareil.

## Défauts connus / prochaines étapes

1. Le « Creuser » libre (question à l'IA) a été supprimé volontairement (coût
   non borné sans auth). Si besoin un jour : fonction serverless + rate limit.
2. Pas d'images (glyphes emoji sur dégradés) — un générateur/banque d'images
   cohérente reste le gros chantier visuel.
3. Dwell tracking IntersectionObserver à valider sur mobile réel.
4. Lancer un premier vrai batch (topics_seed.json, ~11 sujets ≈ 0,09 $).
