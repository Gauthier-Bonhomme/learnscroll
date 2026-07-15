# LearnScroll — État du projet (15/07/2026)

App mobile « TikTok de l'apprentissage » : remplacer le doomscrolling par du
learnscrolling. Feed vertical de cartes de connaissance, chaque swipe apprend
quelque chose en <60 s. **Contrainte produit centrale : app gratuite → l'IA
n'est JAMAIS appelée au runtime du feed ; tout le contenu est généré en amont
par batch et stocké en base.**

## Emplacement & environnement

- Projet : `C:\Users\Gauthier\Desktop\learnscroll\` — **pas de dépôt git initialisé**.
- Machine : Windows 11 ; Python 3.14 et Node 24 installés ; **Flutter ABSENT**.
- Deps pip installées globalement : anthropic, pydantic, sqlalchemy, fastapi, uvicorn.
- Un serveur uvicorn a pu rester actif sur le port 8077 (lancé en arrière-plan).

## Architecture (3 briques)

```
pipeline/ (batch IA) ──écrit──▶ backend/data/learnscroll.db ◀──lit── backend/ (FastAPI) ◀──HTTP── mobile/ (Flutter) + webapp
```

### 1. `pipeline/` — génération batch (CONSTRUIT, testé hors-ligne, jamais lancé contre l'API réelle)

- `config.py` : 3 tiers de modèle — `bulk`=claude-sonnet-5 (défaut, tarif intro 2$/10$ jusqu'au 2026-08-31, env `SONNET5_INTRO=0` après), `flagship`=claude-opus-4-8, `hero`=claude-fable-5. Tout passe par la **Message Batches API (−50 %)**.
- `content_schema.py` : Pydantic `KnowledgeCard` = hook, category (10 catégories sans accents : science, tech, histoire, geopolitique, psychologie, economie, espace, nature, culture, sante), mode (`actualite`|`info`), reading_time (`30s`|`2min`|`5min`), teaser, body, why_layers[] (question/answer), sources[] (title/url), image_prompt, tags. `card_json_schema()` durcit le schéma pour Structured Outputs (additionalProperties=false, required complet ; pas de récursion → arbre « pourquoi » aplati).
- `prompts.py` : `STYLE_GUIDE` éditorial français (system, placé avec `cache_control` → prompt caching) + `user_prompt(topic)`.
- `generate_batch.py` : crée le batch (custom_id stable = idempotence), écrit `.last_batch`. `poll_and_store.py` : poll 30 s, stocke en base (skip si external_id existe).
- `estimate_cost.py` **exécuté** : Sonnet 5 batch = **0,0072 $/carte** (10 000 cartes ≈ 72 $) ; Opus 4.8 = 0,018 $ ; Fable 5 = 0,036 $. Hypothèses : system ~900 tk caché, prompt ~120 tk, sortie ~1400 tk.
- `topics_seed.json` : 11 sujets dont la série « Les Romains » (3 épisodes).
- `_selftest.py` **passé au vert** : schéma durci + validation Pydantic + aller-retour DB.

### 2. `backend/` — FastAPI (CONSTRUIT, tous les endpoints VÉRIFIÉS en direct)

- `app/db.py` : SQLAlchemy, SQLite `backend/data/learnscroll.db` (bascule Postgres via `LEARNSCROLL_DATABASE_URL`). Modèles : `Series`, `Card` (props JSON why_layers/sources/tags ; `to_feed()`/`to_detail()`), `WhyDeepCache`, `Interaction` (kind ∈ view|like|favorite|share|expand, dwell_ms).
- `app/personalization.py` : affinité par catégorie dérivée des interactions (favorite=5, share=4, like=3, expand=2, view=0.3 + bonus dwell) + 25 % d'exploration ; exclut les cartes déjà vues.
- `app/gamification.py` : streak journalier (calculé en UTC), niveaux Curieux(0)→Passionné(25)→Expert(100)→Sage(300), stats (cartes lues, minutes), séries complétées.
- `app/why_service.py` : « J'ai compris… mais pourquoi ? » à la demande → génère avec Sonnet 5 UNE fois par (carte, question), cache en DB ; sans clé API renvoie un message dégradé propre.
- `app/main.py` : `GET /api/feed`, `GET /api/cards/{id}`, `POST /api/cards/{id}/why`, `POST /api/interactions`, `GET /api/favorites`, `GET /api/recommendations/{id}` (même catégorie), `GET /api/profile`, `GET /api/series`, `GET /api/stats` ; monte `/admin` (CMS statique) et `/app` (proto web). CORS `*`.
- `seed_samples.py` : 5 cartes de démo rédigées main (dont Rome ép.1) — **déjà insérées en base**.
- Lancement : `cd backend && python -m uvicorn app.main:app --port 8077`.
- `webapp/index.html` : **prototype web du feed, fonctionnel** — scroll-snap vertical plein écran, DA éditoriale (Fraunces + Inter, fond #0C0B0A, accent ambre #E0A367, teinte + glyphe emoji par catégorie), mode détail glissant, arbre « pourquoi » + champ « Creuser », gamification en topbar, user persisté en localStorage, dwell via IntersectionObserver.
- `admin_ui/index.html` : back-office lecture (stats/séries/cartes) + export de sujets vers `topics_seed.json`. Pas d'auth.
- `.claude/launch.json` créé (serveur `learnscroll-api`, port 8077) — mais les preview tools d'une session ouverte dans le dépôt CV ne le voient pas (ils lisent le launch.json du CV).

### 3. `mobile/` — Flutter (ÉCRIT, JAMAIS COMPILÉ — SDK absent de la machine)

- `pubspec.yaml` : http, google_fonts ; Dart ≥3.6 (usage de `Color.withValues`, Flutter 3.27+).
- `lib/` : `config.dart` (10.0.2.2 pour émulateur Android, override `--dart-define=API_BASE=`), `models.dart`, `api.dart`, `theme.dart` (même DA que la webapp), `main.dart` (NavigationBar 3 onglets), `screens/feed_screen.dart` (PageView vertical + dwell tracking + load more), `detail_screen.dart` (arbre pourquoi + creuser), `favorites_screen.dart`, `profile_screen.dart` (streak/niveau/stats/séries).

## Défauts connus et assumés (avis franc déjà donné à l'utilisateur)

1. **Sources fabriquées** : le prompt demande des « URLs plausibles » → citations hallucinées. À remplacer par ingestion RSS réelle. `fetch_news.py` n'a jamais été écrit (le mode `actualite` n'existe que comme champ).
2. **Flutter : user id aléatoire non persisté** → streaks/favoris/perso perdus à chaque relance (ajouter shared_preferences). La webapp, elle, persiste (localStorage).
3. **Unfavorite pas géré serveur** (interactions append-only, le toggle UI est local).
4. Personnalisation naïve ; placeholder de récence mort (×0.0) dans `personalization.py` ; le feed charge toutes les cartes en mémoire (OK ≤ ~5k cartes).
5. Streak en UTC, pas en fuseau local.
6. Pas d'images (champ `image_prompt` prêt, rien de branché) — glyphes emoji sur dégradés.
7. Pas d'auth ; CORS ouvert ; admin sans auth.

## Verdict donné

Bon projet portfolio (pensée coûts/archi complète). Startup risquée : créneau occupé (Imprint, Perplexity Discover ; Artifact fermé en 2024), « addictif mais éducatif » = tension, sources inventées = disqualifiant pour la confiance. Prochaine étape recommandée : mettre 20 vraies cartes devant 10 personnes, mesurer le retour à J+1.

## Prochaines étapes proposées (non commencées)

1. Ingestion RSS réelle (sources authentiques + mode actualité).
2. Persistance de l'utilisateur côté Flutter (shared_preferences).
3. Toggle favoris côté serveur (kind `unfavorite` ou table dédiée).
4. Génération/sélection d'images éditoriales.
5. Cron de réapprovisionnement du catalogue.
6. `git init` + premier commit (jamais fait).
