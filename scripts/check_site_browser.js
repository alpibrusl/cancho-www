#!/usr/bin/env node
// Load the built site (_site/) in Chromium and check what a static check cannot.
//
//   node scripts/check_site_browser.js [_site] [--shots <dir>]      (needs `playwright` and a Chromium)
//
// For / and /classic/, in light and dark, at 1280 and 412 px wide:
//   - every request is to the site's own origin and answers below 400;
//   - no console error, no page error, no failed request;
//   - exactly one h1, a title, the canonical link; /classic/ fetched data/ecosystem.json;
//   - every internal link resolves (a file answers 200, or the #fragment names an id on the page).
// And: /next/ ends at /; with JavaScript off, / and /classic/ still carry the projects of data/ecosystem.json.
// Exits 1 with the list of problems.
'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const shotsAt = args.indexOf('--shots');
const shots = shotsAt >= 0 ? args.splice(shotsAt, 2)[1] : null;
const dir = path.resolve(args[0] || '_site');
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.md': 'text/markdown; charset=utf-8', '.txt': 'text/plain; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.webp': 'image/webp', '.woff2': 'font/woff2', '.mp4': 'video/mp4', '.webm': 'video/webm', '.cast': 'text/plain' };

function serve() {
  const server = http.createServer((req, res) => {
    let p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    let f = path.join(dir, p);
    if (!f.startsWith(dir)) { res.writeHead(403); return res.end(); }
    if (fs.existsSync(f) && fs.statSync(f).isDirectory()) {
      if (!p.endsWith('/')) { res.writeHead(301, { Location: p + '/' }); return res.end(); }
      f = path.join(f, 'index.html');
    }
    if (!fs.existsSync(f)) { res.writeHead(404); return res.end('not found'); }
    const body = fs.readFileSync(f);
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream', 'Content-Length': body.length });
    res.end(body);
  });
  return new Promise((ok) => server.listen(0, '127.0.0.1', () => ok(server)));
}

(async () => {
  const { chromium } = require('playwright');
  const server = await serve();
  const origin = 'http://127.0.0.1:' + server.address().port;
  const eco = JSON.parse(fs.readFileSync(path.join(dir, 'data/ecosystem.json'), 'utf8'));
  const problems = [];
  const bad = (m) => problems.push(m);
  const browser = await chromium.launch();
  try {
    for (const url of ['/', '/classic/']) {
      for (const scheme of ['light', 'dark']) {
        for (const width of [1280, 412]) {
          const tag = `${url} ${scheme} ${width}`;
          const ctx = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: scheme });
          const page = await ctx.newPage();
          const seen = [];
          page.on('request', (r) => { if (!r.url().startsWith('data:') && !r.url().startsWith('blob:') && !r.url().startsWith('about:')) seen.push(r.url()); });
          page.on('response', (r) => { if (r.status() >= 400) bad(`${tag}: ${r.status()} for ${r.url()}`); });
          page.on('requestfailed', (r) => { if (!/net::ERR_ABORTED/.test(r.failure() ? r.failure().errorText : '')) bad(`${tag}: request failed: ${r.url()} ${r.failure() && r.failure().errorText}`); });
          page.on('console', (m) => { if (m.type() === 'error') bad(`${tag}: console error: ${m.text()}`); });
          page.on('pageerror', (e) => bad(`${tag}: page error: ${e.message}`));
          await page.goto(origin + url, { waitUntil: 'load' });
          await page.waitForLoadState('networkidle').catch(() => {});
          await page.waitForTimeout(800);
          // scroll through, so lazy media and sections are requested
          await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 700) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 40)); } window.scrollTo(0, 0); });
          await page.waitForTimeout(400);
          for (const u of seen) if (!u.startsWith(origin + '/')) bad(`${tag}: request outside the origin: ${u}`);
          // /classic/ draws its map from data/ecosystem.json at run time; the cancho-ui build carries the data in the page.
          if (url === '/classic/' && !seen.some((u) => u === origin + url + 'data/ecosystem.json')) bad(`${tag}: data/ecosystem.json was not fetched`);
          const info = await page.evaluate(() => ({
            title: document.title,
            h1: document.querySelectorAll('h1').length,
            canonical: (document.querySelector('link[rel=canonical]') || {}).href,
            links: [...document.querySelectorAll('a[href]')].map((a) => a.getAttribute('href')),
            ids: [...document.querySelectorAll('[id]')].map((e) => e.id),
            overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          }));
          if (!info.title) bad(`${tag}: no title`);
          if (info.h1 !== 1) bad(`${tag}: ${info.h1} h1`);
          if (info.canonical !== eco.site) bad(`${tag}: canonical ${info.canonical}`);
          if (info.overflow > 0) bad(`${tag}: horizontal overflow of ${info.overflow}px`);
          if (scheme === 'light' && width === 1280) {
            const base = new URL(url, origin);
            for (const href of new Set(info.links)) {
              if (/^(https?:|mailto:|tel:)/.test(href)) continue;
              if (href.startsWith('#')) { if (href.length > 1 && !info.ids.includes(decodeURIComponent(href.slice(1)))) bad(`${tag}: link ${href} names no id`); continue; }
              const target = new URL(href, base);
              if (target.origin !== origin) continue;
              const r = await ctx.request.get(target.href);
              if (r.status() !== 200) bad(`${tag}: link ${href} answers ${r.status()}`);
              if (target.hash && /html$|\/$/.test(target.pathname)) { /* a fragment into another page is not followed */ }
            }
          }
          if (shots) { fs.mkdirSync(shots, { recursive: true }); await page.screenshot({ path: path.join(shots, `${url === '/' ? 'root' : 'classic'}-${scheme}-${width}.png`), fullPage: true }); }
          await ctx.close();
        }
      }
    }
    // /next/ ends at /
    {
      const ctx = await browser.newContext();
      const page = await ctx.newPage();
      await page.goto(origin + '/next/', { waitUntil: 'load' });
      await page.waitForURL(origin + '/', { timeout: 5000 }).catch(() => {});
      if (page.url() !== origin + '/') bad(`/next/ ended at ${page.url()}, expected ${origin}/`);
      await ctx.close();
    }
    // JavaScript off
    for (const url of ['/', '/classic/']) {
      const ctx = await browser.newContext({ javaScriptEnabled: false });
      const page = await ctx.newPage();
      await page.goto(origin + url, { waitUntil: 'load' });
      const text = await page.evaluate(() => document.body.textContent);
      const missing = eco.projects.map((p) => p.name).filter((n) => !text.includes(n));
      if (missing.length) bad(`${url} with JavaScript off: missing projects ${missing.join(', ')}`);
      await ctx.close();
    }
  } finally {
    await browser.close();
    server.close();
  }
  if (problems.length) {
    console.error(`check_site_browser: ${problems.length} problem(s)`);
    for (const p of [...new Set(problems)]) console.error('  - ' + p);
    process.exit(1);
  }
  console.log('check_site_browser: ok (/ and /classic/, light and dark, 1280 and 412; /next/; JavaScript off)');
})().catch((e) => { console.error(e); process.exit(1); });
