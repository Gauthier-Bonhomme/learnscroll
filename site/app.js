/* LearnScroll — application 100 % statique.
 *
 * Tout ce que le backend v1 calculait (personnalisation, gamification,
 * favoris, recommandations) vit ICI, sur l'appareil : localStorage uniquement,
 * aucune donnée n'est envoyée nulle part. Le serveur ne sert que des fichiers.
 */
'use strict';

/* ---------------------------------------------------------------- utils -- */
const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g,
  (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/* Markdown minimal (gras, italique, titres) — le texte est échappé D'ABORD. */
function md(text) {
  const safe = esc(text)
    .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
    .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<i>$2</i>');
  return safe.split(/\n+/).map((p) => p.trim()).filter(Boolean)
    .map((p) => (/^#{1,3}\s/.test(p) ? `<h3>${p.replace(/^#{1,3}\s/, '')}</h3>` : `<p>${p}</p>`))
    .join('');
}

function toast(msg) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toast._h);
  toast._h = setTimeout(() => t.classList.remove('show'), 1600);
}

const GLYPH = { science: '🌅', nature: '🐜', histoire: '🏛️', psychologie: '💭',
  geopolitique: '🌍', economie: '📈', espace: '🪐', tech: '⚙️', sante: '🧬', culture: '🎭' };

function tone(cat) {
  const v = getComputedStyle(document.documentElement).getPropertyValue('--' + cat).trim();
  return v || getComputedStyle(document.documentElement).getPropertyValue('--defaut').trim();
}

/* ------------------------------------------------------- état local ------ */
const store = {
  get(k, fb) { try { const v = JSON.parse(localStorage.getItem('ls.' + k)); return v ?? fb; } catch { return fb; } },
  set(k, v) { try { localStorage.setItem('ls.' + k, JSON.stringify(v)); } catch { /* stockage plein : tant pis */ } },
};
const S = {
  seen: new Set(store.get('seen', [])),
  favs: store.get('favs', []),
  aff: store.get('aff', {}),          // affinité par catégorie
  days: store.get('days', []),        // jours actifs (fuseau LOCAL) -> streak
  views: store.get('views', 0),
  dwellMs: store.get('dwellMs', 0),
};
function persist() {
  store.set('seen', [...S.seen].slice(-5000));
  store.set('favs', S.favs);
  store.set('aff', S.aff);
  store.set('days', S.days.slice(-400));
  store.set('views', S.views);
  store.set('dwellMs', S.dwellMs);
}
function bumpAff(cat, w) { S.aff[cat] = Math.max(0, (S.aff[cat] || 0) + w); }

/* --------------------------------------------------- gamification -------- */
const LEVELS = [[0, 'Curieux'], [25, 'Passionné'], [100, 'Expert'], [300, 'Sage']];
function level() {
  let cur = LEVELS[0], next = null;
  for (const l of LEVELS) { if (S.views >= l[0]) cur = l; else { next = next || l; } }
  return { name: cur[1], next };
}
function dayKey(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
function streak() {
  const days = new Set(S.days);
  if (!days.size) return 0;
  const cur = new Date();
  if (!days.has(dayKey(cur))) cur.setDate(cur.getDate() - 1);   // la série tient jusqu'à demain
  let n = 0;
  while (days.has(dayKey(cur))) { n++; cur.setDate(cur.getDate() - 1); }
  return n;
}
function markActiveToday() {
  const k = dayKey(new Date());
  if (!S.days.includes(k)) S.days.push(k);
}

/* ------------------------------------------------------- topbar ---------- */
function updateTopbar() {
  $('#tStreak').textContent = streak();
  $('#tLevel').textContent = level().name;
  $('#tFavs').textContent = S.favs.length;
}

/* ------------------------------------------------- feed personnalisé ----- */
let INDEX = null;
let ranked = [];          // ordre de présentation
let rendered = 0;
let allSeen = false;
const PAGE = 8;
const feedEl = $('#feed');

/* PRNG déterministe : le feed varie chaque jour, mais reste stable dans la journée. */
function jitter(seedStr) {
  let h = 2166136261;
  for (let i = 0; i < seedStr.length; i++) { h ^= seedStr.charCodeAt(i); h = Math.imul(h, 16777619); }
  return ((h >>> 0) % 1000) / 1000;
}

function buildRanking() {
  const cards = INDEX.cards;                       // déjà trié du plus récent au plus ancien
  const unseen = cards.filter((c) => !S.seen.has(c.id));
  allSeen = unseen.length === 0 && cards.length > 0;
  const pool = allSeen ? cards : unseen;
  const maxAff = Math.max(1, ...Object.values(S.aff));
  const today = dayKey(new Date());

  const scored = pool.map((c, i) => ({
    c,
    s: 0.6 * ((S.aff[c.category] || 0) / maxAff)   // goûts appris
     + 0.25 * (1 - i / pool.length)                // fraîcheur
     + 0.3 * jitter(today + ':' + c.id),           // découverte du jour
  })).sort((a, b) => b.s - a.s);

  /* Diversité : jamais 3 cartes de la même catégorie d'affilée. */
  ranked = [];
  const queue = scored.map((x) => x.c);
  while (queue.length) {
    const n = ranked.length;
    let idx = 0;
    if (n >= 2 && ranked[n - 1].category === ranked[n - 2].category) {
      idx = queue.findIndex((c) => c.category !== ranked[n - 1].category);
      if (idx < 0) idx = 0;
    }
    ranked.push(queue.splice(idx, 1)[0]);
  }
  rendered = 0;
}

function cardHTML(c, first) {
  const g = GLYPH[c.category] || '✨';
  const t = tone(c.category);
  const fav = S.favs.includes(c.id);
  return `<section class="card" data-id="${c.id}" data-cat="${esc(c.category)}">
    <div class="art" style="background:radial-gradient(120% 90% at 50% 12%, ${t} 0%, #0c0b0a 100%)"><div class="glyph">${g}</div></div>
    <div class="content">
      <div class="chips"><span class="chip">${esc(c.category)}</span><span class="chip time">⏱ ${esc(c.reading_time)}</span>${c.mode === 'actualite' ? '<span class="chip">actu</span>' : ''}${c.series ? `<span class="chip">${esc(c.series)}${c.series_index ? ' · ' + c.series_index : ''}</span>` : ''}</div>
      <h2 class="hook">${esc(c.hook)}</h2>
      <p class="teaser">${esc(c.teaser)}</p>
      <div class="rail">
        <button class="discover" data-open="${c.id}">👇 Découvrir</button>
        <button class="act fav ${fav ? 'on' : ''}" data-fav="${c.id}" aria-label="Favori">❤️</button>
        <button class="act" data-share="${c.id}" aria-label="Partager">📤</button>
      </div>
    </div>
    ${first ? '<div class="hint-swipe">glisse vers le haut ↑</div>' : ''}
  </section>`;
}

function allSeenHTML() {
  return `<section class="card allseen">
    <div class="art" style="background:radial-gradient(120% 90% at 50% 12%, var(--defaut) 0%, #0c0b0a 100%)"><div class="glyph">🎓</div></div>
    <div class="content">
      <h2 class="hook">Tu as tout exploré 🎉</h2>
      <p class="teaser">${INDEX.total} cartes lues. Le catalogue se réapprovisionne régulièrement — reviens bientôt, ou repars pour un tour.</p>
      <button class="resetbtn" id="btnReset">Revoir le catalogue</button>
    </div>
  </section>`;
}

function renderMore() {
  if (rendered >= ranked.length) return;
  const slice = ranked.slice(rendered, rendered + PAGE);
  const first = rendered === 0 && !allSeen;
  feedEl.insertAdjacentHTML('beforeend',
    slice.map((c, i) => cardHTML(c, first && i === 0)).join(''));
  rendered += slice.length;
  observeCards();
}

function renderFeed() {
  feedEl.innerHTML = '';
  if (!INDEX.cards.length) {
    feedEl.innerHTML = `<div class="empty"><b>Catalogue vide.</b>
      <span>Génère du contenu : <code>python seed_samples.py</code> puis <code>python export_site.py</code></span></div>`;
    return;
  }
  if (allSeen) feedEl.insertAdjacentHTML('beforeend', allSeenHTML());
  renderMore();
}

/* ------------------------------------------- vues + temps passé ---------- */
const dwellStart = {};
let io = null;
function observeCards() {
  if (io) io.disconnect();
  io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      const el = e.target;
      const id = +el.dataset.id;
      if (!id) return;
      if (e.isIntersecting) {
        dwellStart[id] = Date.now();
        /* Pagination : on approche de la fin -> on ajoute une page. */
        const idx = ranked.findIndex((c) => c.id === id);
        if (idx >= rendered - 3) renderMore();
      } else if (dwellStart[id]) {
        const ms = Date.now() - dwellStart[id];
        delete dwellStart[id];
        if (ms > 1200) markSeen(id, el.dataset.cat, ms);
      }
    });
  }, { threshold: 0.6 });
  document.querySelectorAll('.card[data-id]').forEach((c) => io.observe(c));
}

function markSeen(id, cat, ms) {
  if (!S.seen.has(id)) { S.seen.add(id); S.views += 1; }
  S.dwellMs += ms;
  bumpAff(cat, 0.3 + Math.min(ms / 45000, 1) * 2);
  markActiveToday();
  persist();
  updateTopbar();
}

/* ------------------------------------------------------ favoris ---------- */
function toggleFav(id, btn) {
  const i = S.favs.indexOf(id);
  const card = INDEX.cards.find((c) => c.id === id);
  if (i >= 0) {
    S.favs.splice(i, 1);
    if (card) bumpAff(card.category, -5);
    toast('Retiré des favoris');
  } else {
    S.favs.push(id);
    if (card) bumpAff(card.category, 5);
    toast('Ajouté aux favoris ❤️');
  }
  if (btn) btn.classList.toggle('on', i < 0);
  persist();
  updateTopbar();
}

/* ------------------------------------------------------ partage ---------- */
async function share(id) {
  const card = INDEX.cards.find((c) => c.id === id);
  const url = location.href.split('#')[0] + '#c/' + id;
  if (card) { bumpAff(card.category, 4); persist(); }
  if (navigator.share) {
    try { await navigator.share({ title: 'LearnScroll', text: card ? card.hook : '', url }); } catch { /* annulé */ }
  } else if (navigator.clipboard) {
    await navigator.clipboard.writeText(url);
    toast('Lien copié 📋');
  }
}

/* ------------------------------------------------------- détail ---------- */
const expanded = new Set();   // 1 signal d'affinité par carte et par session

async function openDetail(id, pushHash = true) {
  let d;
  try {
    d = await (await fetch(`data/cards/${id}.json`)).json();
  } catch { toast('Carte indisponible hors-ligne'); return; }

  if (!expanded.has(id)) { expanded.add(id); bumpAff(d.category, 2); persist(); }

  const seriesChip = d.series
    ? `<span class="chip">${esc(d.series)}${d.series_index ? ` · épisode ${d.series_index}${d.series_total ? '/' + d.series_total : ''}` : ''}</span>` : '';
  const sources = (d.sources || [])
    .filter((s) => /^https?:\/\//.test(s.url || ''))
    .map((s) => `<a href="${esc(s.url)}" target="_blank" rel="noopener">↗ ${esc(s.title)}</a>`).join('');
  const related = (d.related || []).map((r) => `
    <button class="relcard" data-open="${r.id}">
      <span class="dot" style="background:${tone(r.category)}"></span>
      <span>${esc(r.hook)}<small>${esc(r.category)} · ⏱ ${esc(r.reading_time)}</small></span>
    </button>`).join('');

  $('#detailBody').innerHTML = `
    <div class="chips"><span class="chip">${esc(d.category)}</span><span class="chip time">⏱ ${esc(d.reading_time)}</span>${d.mode === 'actualite' ? '<span class="chip">actu</span>' : ''}${seriesChip}</div>
    <h1>${esc(d.hook)}</h1>
    <div class="body">${md(d.body)}</div>
    <div id="whyZone" data-layers='${esc(JSON.stringify(d.why_layers || []))}'>
      ${(d.why_layers || []).length ? `<button class="whybtn" data-why="0">💡 J'ai compris… mais pourquoi ?</button>` : ''}
    </div>
    ${related ? `<div class="related"><h3>Continuer à creuser</h3><div class="relgrid">${related}</div></div>` : ''}
    ${sources ? `<div class="sources"><h3>Sources</h3>${sources}</div>` : ''}`;

  $('#detail').classList.add('open');
  $('#detail').scrollTop = 0;
  if (pushHash && location.hash !== '#c/' + id) location.hash = 'c/' + id;
}

/* Révélation progressive : chaque clic dévoile UNE couche de plus. */
function revealWhy(btn) {
  const zone = $('#whyZone');
  const layers = JSON.parse(zone.dataset.layers || '[]');
  const i = +btn.dataset.why;
  if (i >= layers.length) return;
  const l = layers[i];
  btn.remove();
  zone.insertAdjacentHTML('beforeend',
    `<div class="layer"><div class="q">${esc(l.question)}</div><div class="a">${esc(l.answer)}</div></div>`
    + (i + 1 < layers.length
      ? `<button class="whybtn" data-why="${i + 1}">🌀 Mais pourquoi ? (${i + 2}/${layers.length})</button>`
      : ''));
}

function hideDetail() { $('#detail').classList.remove('open'); }
function closeDetail() {
  if (/^#c\//.test(location.hash)) history.back();
  else hideDetail();
}

/* ---------------------------------------------------- panneau ------------ */
function openSheet(kind) {
  $('#sheetTitle').textContent = kind === 'favs' ? 'Mes favoris' : 'Ma progression';
  $('#sheetBody').innerHTML = kind === 'favs' ? favsHTML() : profileHTML();
  $('#sheet').classList.add('open');
}
function favsHTML() {
  if (!S.favs.length) return `<div class="sheetEmpty">Aucun favori pour l'instant.<br>Touche ❤️ sur une carte qui te plaît.</div>`;
  return S.favs.map((id) => {
    const c = INDEX.cards.find((x) => x.id === id);
    if (!c) return '';
    return `<div class="favRow" data-open="${c.id}">
      <span class="dot" style="background:${tone(c.category)}"></span>
      <span class="t">${esc(c.hook)}<small>${esc(c.category)} · ⏱ ${esc(c.reading_time)}</small></span>
      <button class="rm" data-unfav="${c.id}" aria-label="Retirer">✕</button>
    </div>`;
  }).join('');
}
function profileHTML() {
  const lv = level();
  const mins = Math.round(S.dwellMs / 60000);
  const next = lv.next
    ? `<div class="lvlbar"><i style="width:${Math.min(100, S.views / lv.next[0] * 100)}%"></i></div>
       <span style="color:var(--mut);font-size:12.5px">${lv.next[0] - S.views} cartes avant « ${lv.next[1]} »</span>`
    : `<span style="color:var(--mut);font-size:12.5px">Niveau maximum atteint 🎓</span>`;
  const series = (INDEX.series || []).map((sr) => {
    const done = sr.card_ids.filter((id) => S.seen.has(id)).length;
    const complete = done >= sr.total;
    return `<div class="serieRow">
      <div class="n"><b>${complete ? '✓ ' : ''}${esc(sr.name)}</b><span>${done}/${sr.total}</span></div>
      <div class="lvlbar"><i style="width:${Math.min(100, done / sr.total * 100)}%"></i></div>
    </div>`;
  }).join('');
  return `
    <div class="statgrid">
      <div class="stat"><b>🔥 ${streak()}</b><span>jours d'affilée</span></div>
      <div class="stat"><b>${lv.name}</b><span>${S.views} cartes lues</span>${next}</div>
      <div class="stat"><b>${mins}</b><span>minutes apprises</span></div>
      <div class="stat"><b>${S.favs.length}</b><span>favoris</span></div>
    </div>
    ${series ? `<h3 style="font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);margin-top:22px">Séries</h3>${series}` : ''}
    <p style="color:var(--mut);font-size:12.5px;margin-top:22px">Tout est stocké sur ton appareil. Aucune donnée ne quitte ton téléphone.</p>`;
}

/* --------------------------------------------------- navigation ---------- */
function route() {
  const m = location.hash.match(/^#c\/(\d+)$/);
  if (m) openDetail(+m[1], false);
  else hideDetail();
}

/* --------------------------------------------------- événements ---------- */
document.addEventListener('click', (e) => {
  const t = e.target.closest('[data-open],[data-fav],[data-share],[data-unfav],[data-why],#btnReset');
  if (!t) return;
  if (t.dataset.open) { $('#sheet').classList.remove('open'); openDetail(+t.dataset.open); }
  else if (t.dataset.fav) toggleFav(+t.dataset.fav, t);
  else if (t.dataset.share) share(+t.dataset.share);
  else if (t.dataset.unfav) { toggleFav(+t.dataset.unfav, null); $('#sheetBody').innerHTML = favsHTML(); }
  else if (t.dataset.why !== undefined) revealWhy(t);
  else if (t.id === 'btnReset') { S.seen.clear(); persist(); buildRanking(); renderFeed(); feedEl.scrollTop = 0; }
});
$('#btnBack').addEventListener('click', closeDetail);
$('#btnFavs').addEventListener('click', () => openSheet('favs'));
$('#btnProfile').addEventListener('click', () => openSheet('profile'));
$('#btnCloseSheet').addEventListener('click', () => $('#sheet').classList.remove('open'));
$('#sheet').addEventListener('click', (e) => { if (e.target.id === 'sheet') $('#sheet').classList.remove('open'); });
window.addEventListener('hashchange', route);

/* -------------------------------------------------------- boot ----------- */
async function boot() {
  try {
    INDEX = await (await fetch('data/index.json')).json();
  } catch {
    feedEl.innerHTML = `<div class="empty"><b>Contenu inaccessible.</b>
      <span>Vérifie ta connexion, puis recharge.</span></div>`;
    return;
  }
  buildRanking();
  renderFeed();
  updateTopbar();
  route();
}
boot();

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js').catch(() => { /* http local : ok */ });
}
