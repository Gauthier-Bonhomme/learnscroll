/* LearnScroll — service worker : app installable et lisible hors-ligne.
 * Stratégies :
 *   - coquille (html/css/js/icône)  : cache d'abord (pré-chargée à l'install)
 *   - data/index.json               : réseau d'abord (contenu frais), cache en secours
 *   - data/cards/*.json, polices    : cache d'abord, mise en cache au fil de l'eau
 */
'use strict';

const VERSION = 'ls-v2';
const SHELL = ['./', 'index.html', 'styles.css', 'app.js', 'manifest.webmanifest', 'icon.svg'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  if (url.pathname.endsWith('/data/index.json')) {
    e.respondWith(
      fetch(req)
        .then((resp) => {
          const copy = resp.clone();
          caches.open(VERSION).then((c) => c.put(req, copy));
          return resp;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  e.respondWith(
    caches.match(req).then((hit) => hit || fetch(req).then((resp) => {
      if (resp.ok || resp.type === 'opaque') {
        const copy = resp.clone();
        caches.open(VERSION).then((c) => c.put(req, copy));
      }
      return resp;
    }))
  );
});
