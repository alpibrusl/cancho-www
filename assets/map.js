/* The ecosystem map, drawn like a walkers' map of La Pedriza: parchment, green forest patches, pink granite, dashed
   footpaths, a river, a road, handwritten names. Layout only: size, distance, footpaths and rivers mean nothing.
   The one line that does mean something is the blue arrow, "rests on". Reads data/ecosystem.json. */
(function () {
  'use strict';
  var R = window.Rocks, el = R.el;
  var $ = function (s, c) { return (c || document).querySelector(s); };

  // [x, y, where the name goes]: s = under the rock; n, e, w = beside it, joined by a thin line
  var SPOTS = {
    cancho: [280, 505, 'n'], 'cancho-ui': [250, 710, 'e'],
    'cancho-forge': [405, 255, 'w'], 'cancho-cache': [560, 335, 's'], 'cancho-hooks': [705, 255, 'n'], 'cancho-gateway': [855, 335, 's'], 'cancho-mqtt': [995, 255, 'n'], 'cancho-dns': [1120, 335, 's'], 'cancho-oci': [1215, 245, 'n'],
    'cancho-schema': [560, 485, 's'], 'cancho-web': [745, 550, 's'], 'cancho-pg': [905, 485, 'n'], 'cancho-log': [1050, 550, 's'], 'cancho-stats': [1170, 465, 'n'], 'cancho-ml': [1200, 600, 's'], 'cancho-mqtt-client': [415, 615, 'w'],
    'cancho-tools': [535, 775, 'w'], 'cancho-table': [690, 775, 's'], 'cancho-client-gen': [855, 775, 's'], 'cancho-code': [610, 865, 's'], 'cancho-fetch': [775, 865, 's'],
    'cancho-robot': [1030, 775, 'n'], 'cancho-gpu': [1170, 775, 'n'], 'cancho-hdl': [1100, 865, 's']
  };
  var REGIONS = [['La Pedriza', 120, 205], ['Services', 420, 150], ['Libraries', 640, 392], ['Tools', 345, 872], ['Edge', 1190, 888]];
  var PARKING = [112, 652];
  var ROAD = 'M20,130 C50,300 15,470 52,600 C92,705 230,800 420,892';
  var RIVER = 'M96,110 C130,260 90,420 125,560 C160,690 300,790 470,860 C560,895 600,900 700,905';
  var FOREST = [[300, 470, 190, 110], [620, 330, 250, 90], [880, 500, 260, 110], [1090, 330, 150, 90], [620, 790, 230, 90], [1080, 790, 170, 90], [240, 690, 100, 60]];

  function blob(r, cx, cy, rx, ry, n, jitter) {
    return R.smooth(R.outline(r, rx, ry, n, jitter, 0.78).map(function (p) { return [p[0] + cx, p[1] + cy]; }));
  }

  /* One outcrop of granite: a main boulder (shaded, with a highlight) and a few pebbles around it. */
  function granite(parent, o) {
    var r = R.rng(R.hash(o.seed)), g = el('g', { class: 'granite' }, parent);
    var ry = o.ry * 0.78, cy = o.baseY - ry * 0.78;
    if (!o.design) el('ellipse', { cx: o.x + o.rx * 0.1, cy: o.baseY + 2, rx: o.rx * 1.1, ry: Math.max(4, ry * 0.16), class: 'g-shadow' }, g);
    var pebbles = o.big ? 8 : 2 + (R.hash(o.seed) % 4);
    for (var i = 0; i < pebbles; i++) {
      var a = r() * Math.PI * 2, d = o.rx * (1.05 + r() * 0.55), pr = 3 + r() * (o.big ? 9 : 6);
      el('path', { d: blob(r, o.x + Math.cos(a) * d, o.baseY - pr * 0.6 + Math.sin(a) * ry * 0.5, pr * 1.3, pr * 0.8, 8, 0.2), class: 'g-body g-pebble' }, g);
    }
    var d = blob(r, o.x, cy, o.rx, ry, o.big ? 15 : 11, o.big ? 0.08 : 0.15);
    el('path', { d: d, class: 'g-body' }, g);
    if (!o.design) {
      el('path', { d: d, class: 'g-shade' }, g);
      el('ellipse', { cx: o.x - o.rx * 0.3, cy: cy - ry * 0.42, rx: o.rx * 0.28, ry: ry * 0.14, class: 'g-light', transform: 'rotate(-12 ' + (o.x - o.rx * 0.3) + ' ' + (cy - ry * 0.42) + ')' }, g);
      for (var k = 0; k < (o.big ? 4 : 1); k++) {
        var x0 = o.x + (r() - 0.5) * o.rx * 0.9, y0 = cy - ry * (0.1 + r() * 0.35);
        el('path', { d: 'M' + x0.toFixed(1) + ',' + y0.toFixed(1) + 'q' + ((r() - 0.5) * o.rx * 0.3).toFixed(1) + ',' + (ry * 0.25).toFixed(1) + ' ' + ((r() - 0.5) * o.rx * 0.35).toFixed(1) + ',' + (ry * 0.5).toFixed(1), class: 'g-crack' }, g);
      }
    }
    return g;
  }

  /* A footpath between two places: a few wobbling waypoints through a smooth curve. */
  function trail(parent, r, a, b, cls) {
    var dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len;
    var sx = a.x + ux * (a.rx || 20) * 0.9, sy = a.y - (a.ry || 10) * 0.4 + uy * (a.ry || 10) * 0.5;
    var ex = b.x - ux * (b.rx || 20) * 0.9, ey = b.y - (b.ry || 10) * 0.4 - uy * (b.ry || 10) * 0.4;
    var pts = [[sx, sy]];
    for (var i = 1; i <= 3; i++) {
      var t = i / 4, off = (r() - 0.5) * Math.min(60, len * 0.25);
      pts.push([sx + (ex - sx) * t - uy * off, sy + (ey - sy) * t + ux * off]);
    }
    pts.push([ex, ey]);
    var d = 'M' + pts[0][0].toFixed(1) + ',' + pts[0][1].toFixed(1);
    for (var j = 0; j < pts.length - 1; j++) {
      var p0 = pts[Math.max(0, j - 1)], p1 = pts[j], p2 = pts[j + 1], p3 = pts[Math.min(pts.length - 1, j + 2)];
      d += 'C' + (p1[0] + (p2[0] - p0[0]) / 6).toFixed(1) + ',' + (p1[1] + (p2[1] - p0[1]) / 6).toFixed(1) + ' ' + (p2[0] - (p3[0] - p1[0]) / 6).toFixed(1) + ',' + (p2[1] - (p3[1] - p1[1]) / 6).toFixed(1) + ' ' + p2[0].toFixed(1) + ',' + p2[1].toFixed(1);
    }
    return el('path', { d: d, class: cls }, parent);
  }

  function draw(data, demos) {
    demos = demos || {};
    var svg = $('#map-svg');
    if (!svg) return;
    var defs = el('defs', {}, svg);
    var gg = el('linearGradient', { id: 'gran', x1: 0, y1: 0, x2: 0.8, y2: 1 }, defs);
    [[0, 'var(--gr1)'], [0.55, 'var(--gr2)'], [1, 'var(--gr3)']].forEach(function (s) { el('stop', { offset: s[0], style: 'stop-color:' + s[1] }, gg); });
    var gs = el('radialGradient', { id: 'gran-shade', cx: 0.3, cy: 0.2, r: 1 }, defs);
    [[0, 0], [0.6, 0], [1, 0.32]].forEach(function (s) { el('stop', { offset: s[0], 'stop-color': '#3a1d14', 'stop-opacity': s[1] }, gs); });
    var blur = el('filter', { id: 'soft', x: '-30%', y: '-30%', width: '160%', height: '160%' }, defs);
    el('feGaussianBlur', { stdDeviation: 22 }, blur);
    var grain = el('filter', { id: 'paper', x: 0, y: 0, width: '100%', height: '100%' }, defs);
    el('feTurbulence', { type: 'fractalNoise', baseFrequency: 0.8, numOctaves: 2, seed: 4, result: 'n' }, grain);
    el('feColorMatrix', { in: 'n', type: 'matrix', values: '0 0 0 0 0.35  0 0 0 0 0.28  0 0 0 0 0.12  0 0 0 0.09 0' }, grain);

    // paper, with a little grain, and the forest as soft green patches
    el('rect', { x: 0, y: 100, width: 1300, height: 810, class: 'paper' }, svg);
    el('rect', { x: 0, y: 100, width: 1300, height: 810, filter: 'url(#paper)', class: 'grain' }, svg);
    var fg = el('g', { filter: 'url(#soft)', class: 'forest' }, svg);
    FOREST.forEach(function (f) { el('ellipse', { cx: f[0], cy: f[1], rx: f[2], ry: f[3] }, fg); });

    // river and road, each with a name along it
    el('path', { d: RIVER, class: 'river' }, svg);
    var road = el('g', { class: 'road' }, svg);
    el('path', { d: ROAD, class: 'road-edge' }, road);
    el('path', { id: 'road-path', d: ROAD, class: 'road-fill' }, road);
    el('textPath', { href: '#road-path', startOffset: '4%' }, el('text', { class: 'road-name' }, road)).textContent = 'github.com / alpibrusl';
    el('path', { id: 'river-path', d: RIVER, fill: 'none' }, svg);
    var rn = el('text', { class: 'river-name' }, svg);
    el('textPath', { href: '#river-path', startOffset: '17%' }, rn).textContent = 'Río Manzanares';

    REGIONS.forEach(function (r) { el('text', { x: r[1], y: r[2], class: 'region' }, svg).textContent = r[0]; });
    // a few houses, because there is a village at the bottom of every walk
    var vil = el('g', { class: 'village' }, svg), vr = R.rng(21);
    for (var h = 0; h < 14; h++) el('rect', { x: 95 + (h % 5) * 14 + vr() * 6, y: 812 + Math.floor(h / 5) * 14 + vr() * 5, width: 8 + vr() * 5, height: 7 + vr() * 4 }, vil);
    el('text', { x: 135, y: 803, class: 'name sub', style: 'text-anchor:middle' }, svg).textContent = 'Manzanares el Real';

    var na = el('g', { class: 'north', transform: 'translate(1262,705)' }, svg);
    el('path', { d: 'M0,26 L0,-16 M-7,-6 L0,-18 L7,-6', class: 'north-line' }, na);
    el('text', { x: 0, y: -24, style: 'text-anchor:middle' }, na).textContent = 'N';

    var pos = {}, spare = 0;
    data.projects.forEach(function (p) {
      var big = p.id === 'cancho', s = SPOTS[p.id] || [100 + (spare++) * 120, 890, 's'];
      pos[p.id] = { p: p, x: s[0], y: s[1], dir: s[2], big: big, rx: big ? 118 : 46 + (R.hash(p.id) % 14), ry: big ? 88 : 34 + (R.hash(p.id + 'y') % 10) };
    });

    // green footpaths: each place to its two nearest neighbours (and the car park), purely decorative
    var tg = el('g', { class: 'trails' }, svg), tr = R.rng(5), ids = Object.keys(pos), seen = {};
    var nodes = ids.map(function (id) { return pos[id]; }).concat([{ x: PARKING[0] + 12, y: PARKING[1] + 30, rx: 12, ry: 8, id: 'P' }]);
    nodes.forEach(function (a) {
      nodes.filter(function (b) { return b !== a; })
        .sort(function (u, v) { return Math.hypot(u.x - a.x, (u.y - a.y) * 1.2) - Math.hypot(v.x - a.x, (v.y - a.y) * 1.2); })
        .slice(0, 2).forEach(function (b) {
          var key = [a.id || a.p.id, b.id || b.p.id].sort().join('|');
          if (!seen[key]) { seen[key] = 1; trail(tg, tr, a, b, 'trail'); }
        });
    });

    // the car park is this page
    var pk = el('a', { href: 'https://github.com/alpibrusl/cancho-www', class: 'park' }, svg);
    el('rect', { x: PARKING[0], y: PARKING[1], width: 24, height: 24, rx: 3 }, pk);
    el('text', { x: PARKING[0] + 12, y: PARKING[1] + 18, class: 'park-p', style: 'text-anchor:middle' }, pk).textContent = 'P';
    el('text', { x: PARKING[0] + 12, y: PARKING[1] - 8, class: 'name', style: 'text-anchor:middle' }, pk).textContent = 'cancho-www';
    el('text', { x: PARKING[0] + 12, y: PARKING[1] + 44, class: 'name sub', style: 'text-anchor:middle' }, pk).textContent = 'you are here';

    // the one meaningful line: rests on
    var lines = el('g', {}, svg), restLines = [];
    var mk = el('marker', { id: 'mk-rest', viewBox: '0 0 10 10', refX: 8, refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse' }, defs);
    el('path', { d: 'M0,0L10,5L0,10z', class: 'mk-rest' }, mk);
    data.projects.forEach(function (p) {
      (p.rests_on || []).forEach(function (t) {
        if (!pos[t]) return;
        var a = pos[p.id], b = pos[t];
        restLines.push(el('path', { d: 'M' + a.x + ',' + (a.y - a.ry * 1.2) + 'Q' + ((a.x + b.x) / 2) + ',' + (Math.min(a.y, b.y) - 110) + ' ' + b.x + ',' + (b.y - b.ry * 1.5), class: 'rests', 'marker-end': 'url(#mk-rest)', 'data-a': p.id, 'data-b': t }, lines));
      });
    });

    var rocks = [], detail = $('#detail');
    Object.keys(pos).sort(function (a, b) { return pos[a].y - pos[b].y; }).forEach(function (id) {
      var q = pos[id], p = q.p, design = p.stage === 'design';
      var g = el('g', { class: 'rock ' + (design ? 'design' : 'built'), tabindex: 0, role: 'button', 'aria-label': p.name + ', ' + p.stage + ': ' + p.summary, 'data-id': id, 'data-kind': p.kind }, svg);
      var inner = el('g', { class: 'inner' }, g);
      granite(inner, { seed: p.id, x: q.x, baseY: q.y, rx: q.rx, ry: q.ry, big: q.big, design: design });
      el('circle', { cx: q.x + q.rx * 0.62, cy: q.y - q.ry * 1.3, r: 5, class: 'pin ' + p.stage }, inner);
      var top = q.y - q.ry * 1.45, mid = q.y - q.ry * 0.55, cls = 'name' + (q.big ? ' big' : '');
      if (q.dir === 's') {
        el('text', { x: q.x, y: q.y + 21, class: cls, style: 'text-anchor:middle' }, g).textContent = p.name;
      } else if (q.dir === 'n') {
        el('text', { x: q.x, y: top - 14, class: cls, style: 'text-anchor:middle' }, g).textContent = p.name;
        el('path', { d: 'M' + q.x + ',' + (top - 9) + ' L' + q.x + ',' + (top + 2), class: 'leader' }, g);
      } else {
        var sgn = q.dir === 'e' ? 1 : -1, edge = q.x + sgn * q.rx * 1.02;
        el('text', { x: edge + sgn * 34, y: mid + 4, class: cls, style: 'text-anchor:' + (sgn > 0 ? 'start' : 'end') }, g).textContent = p.name;
        el('path', { d: 'M' + (edge + sgn * 30) + ',' + mid + ' L' + (edge + sgn * 2) + ',' + mid, class: 'leader' }, g);
      }
      g.addEventListener('click', function () { select(id); });
      g.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(id); } });
      rocks.push(g);
    });


    /* The walk: a hiker leaves the car park, the camera follows to the rock, and the recorded session types out beside it. */
    var vb0 = svg.getAttribute('viewBox'), walking = 0, reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    function vbTo(to, ms, done) {
      var from = svg.getAttribute('viewBox').split(' ').map(Number), t0 = null;
      if (reduce) { svg.setAttribute('viewBox', to.join(' ')); if (done) done(); return; }
      (function f(t) {
        if (t0 === null) t0 = t;
        var k = Math.min(1, (t - t0) / ms), e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
        svg.setAttribute('viewBox', from.map(function (v, i) { return (v + (to[i] - v) * e).toFixed(1); }).join(' '));
        if (k < 1) requestAnimationFrame(f); else if (done) done();
      })(performance.now());
    }
    function resetView() { walking++; var h = svg.querySelector('.hiker'); if (h) h.remove(); vbTo(vb0.split(' ').map(Number), 500); }
    /* One walker for both kinds of demo. A rock's session is one stop; a trail is a route of several, and each step
       happens at the rock it names (`at`), so the hiker walks there before the command types. */
    function stop(from, q, me, done) {
      var path = el('path', { d: 'M' + from[0] + ',' + from[1] + 'Q' + ((from[0] + q.x) / 2) + ',' + (Math.max(from[1], q.y) + 70) + ' ' + q.x + ',' + (q.y + 6), fill: 'none', class: 'walk-path' }, svg);
      var hk = svg.querySelector('.hiker');
      if (!hk) { hk = el('g', { class: 'hiker' }, svg); el('circle', { r: 7, class: 'hiker-dot' }, hk); el('circle', { r: 14, class: 'hiker-halo' }, hk); }
      hk.classList.remove('rest');
      var len = path.getTotalLength(), w = 460, h = w * 810 / 1300;
      vbTo([Math.max(0, q.x - w / 2), Math.max(100, q.y - h * .6), w, h], reduce ? 0 : 1400);
      rocks.forEach(function (g) { g.classList.toggle('sel', g.getAttribute('data-id') === q.id); });
      requestAnimationFrame(function f0(t0) {
        (function f(t) {
          if (me !== walking) return;
          var k = reduce ? 1 : Math.min(1, (t - t0) / 1400), pt = path.getPointAtLength(len * k);
          hk.setAttribute('transform', 'translate(' + pt.x + ',' + pt.y + ')');
          if (k < 1) requestAnimationFrame(f); else { path.remove(); hk.classList.add('rest'); done(); }
        })(t0);
      });
    }
    /* A chart in the panel, drawn from the numbers a tool printed (the recorder copies them into the session). */
    function chartBox(c) {
      var W = 240, H = 176, L = 28, R = 8, T = 30, B = 32, pw = W - L - R, ph = H - T - B;
      var box = document.createElement('div'); box.className = 't-chart';
      var svg2 = el('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', class: 'chart' }, box);
      function fmt(v) { return Math.abs(v) >= 100 ? v.toFixed(0) : (Math.round(v * 10) / 10).toString(); }
      el('text', { x: 4, y: 13, class: 'ch-title' }, svg2).textContent = c.short || c.title;
      var sum;
      if (c.type === 'histogram') {
        var mx = Math.max.apply(null, c.counts), n = c.counts.length, bw = pw / n;
        c.counts.forEach(function (k, i) {
          var h = mx ? (ph * k) / mx : 0;
          el('rect', { x: (L + i * bw + 1).toFixed(1), y: (T + ph - h).toFixed(1), width: (bw - 2).toFixed(1), height: h.toFixed(1), class: 'ch-bar' }, svg2);
          if (k) el('text', { x: (L + i * bw + bw / 2).toFixed(1), y: (T + ph - h - 3).toFixed(1), class: 'ch-n', style: 'text-anchor:middle' }, svg2).textContent = k;
        });
        el('path', { d: 'M' + L + ',' + (T + ph) + 'H' + (L + pw), class: 'ch-axis' }, svg2);
        [0, n].forEach(function (i) { el('text', { x: L + i * bw, y: H - 14, class: 'ch-tick', style: 'text-anchor:' + (i ? 'end' : 'start') }, svg2).textContent = fmt(c.edges[i]); });
        el('text', { x: L + pw / 2, y: H - 3, class: 'ch-tick', style: 'text-anchor:middle' }, svg2).textContent = c.unit + ', ' + n + ' equal bins; bar = count';
        sum = c.title + ': ' + c.counts.join(', ') + ' readings in each of ' + n + ' bins from ' + fmt(c.edges[0]) + ' to ' + fmt(c.edges[n]) + ' ' + c.unit + '.';
      } else if (c.type === 'bars') {
        var bh = (ph + 14) / c.values.length;
        c.values.forEach(function (v, i) {
          var y = 18 + i * bh + 12;
          el('text', { x: 4, y: y - 3, class: 'ch-tick' }, svg2).textContent = c.labels[i];
          el('rect', { x: 4, y: y, width: Math.max(1, (W - 8 - 40) * v).toFixed(1), height: 12, class: 'ch-bar' }, svg2);
          el('text', { x: (4 + (W - 8 - 40) * v + 4).toFixed(1), y: y + 10, class: 'ch-n' }, svg2).textContent = String(Math.round(v * 1000) / 1000);
        });
        sum = c.title + ': ' + c.labels.map(function (l, i) { return l + ' ' + Math.round(c.values[i] * 1000) / 1000; }).join('; ') + '.';
      } else {
        var vals = c.points.reduce(function (a, p) { return a.concat(p); }, []), lo = Math.floor(Math.min.apply(null, vals) * 2) / 2, hi = Math.ceil(Math.max.apply(null, vals) * 2) / 2;
        function X(v) { return L + ((v - lo) / (hi - lo)) * pw; } function Y(v) { return T + ph - ((v - lo) / (hi - lo)) * ph; }
        el('path', { d: 'M' + L + ',' + T + 'V' + (T + ph) + 'H' + (L + pw), class: 'ch-axis' }, svg2);
        el('path', { d: 'M' + X(lo) + ',' + Y(lo) + 'L' + X(hi) + ',' + Y(hi), class: 'ch-diag' }, svg2);
        c.points.forEach(function (p) { el('circle', { cx: X(p[0]).toFixed(1), cy: Y(p[1]).toFixed(1), r: 3.2, class: 'ch-dot' }, svg2); });
        [lo, hi].forEach(function (v) {
          el('text', { x: X(v), y: H - 14, class: 'ch-tick', style: 'text-anchor:' + (v === lo ? 'start' : 'end') }, svg2).textContent = fmt(v);
          el('text', { x: L - 4, y: Y(v) + 3, class: 'ch-tick', style: 'text-anchor:end' }, svg2).textContent = fmt(v);
        });
        el('text', { x: L + pw / 2, y: H - 3, class: 'ch-tick', style: 'text-anchor:middle' }, svg2).textContent = 'actual ' + c.unit + ' across, predicted up';
        sum = c.title + ': ' + c.points.length + ' points; the dashed line is where predicted equals actual.';
      }
      svg2.setAttribute('aria-label', sum);
      return box;
    }
    function demoUI(key, id) {
      var d = demos[key], trail = !!d.route;
      var box = document.createElement('div'); box.className = 'demo';
      var head = document.createElement('div'); head.className = 'demo-head';
      var t = document.createElement('strong'); t.textContent = d.title; head.appendChild(t);
      var go = document.createElement('button'); go.type = 'button'; go.className = 'btn primary walk'; go.textContent = trail ? 'Walk the trail ▸' : 'Walk here ▸'; head.appendChild(go);
      var back = document.createElement('button'); back.type = 'button'; back.className = 'btn ghost walk'; back.textContent = 'Whole map'; back.addEventListener('click', resetView); head.appendChild(back);
      var term = document.createElement('div'); term.className = 'term'; term.setAttribute('role', 'log'); term.setAttribute('aria-label', 'Recorded session: ' + d.title);
      var note = document.createElement('p'); note.className = 'fine'; note.textContent = d.source || 'A recorded run of the real tools, replayed. scripts/record_demos.py writes it.';
      box.appendChild(head); box.appendChild(term); box.appendChild(note); detail.appendChild(box);
      function line(cls, text) { var l = document.createElement('div'); l.className = cls; l.textContent = text; term.appendChild(l); return l; }
      d.steps.forEach(function (st) { if (st.note) line('t-note', '# ' + st.note); line('t-cmd', '$ ' + st.cmd); if (st.out) line('t-out', st.out); if (st.chart) term.appendChild(chartBox(st.chart)); });
      go.addEventListener('click', function () {
        var me = ++walking, i = 0, here = [PARKING[0] + 12, PARKING[1] + 30], hk0 = svg.querySelector('.hiker'); if (hk0) hk0.remove();
        svg.querySelectorAll('.walk-path').forEach(function (n) { n.remove(); });
        term.textContent = ''; go.disabled = true;
        (function next() {
          if (me !== walking) return;
          if (i >= d.steps.length) { go.disabled = false; go.textContent = 'Walk again ▸'; return; }
          var st = d.steps[i++], at = st.at || id;
          function type() {
            if (st.note) line('t-note', '# ' + st.note);
            var c = line('t-cmd', '$ '), n = 0;
            (function tick() {
              if (me !== walking) return;
              if (n < st.cmd.length) { n += reduce ? st.cmd.length : 2; c.textContent = '$ ' + st.cmd.slice(0, n); setTimeout(tick, 22); }
              else { setTimeout(function () { if (st.out) line('t-out', st.out); if (st.chart) term.appendChild(chartBox(st.chart)); term.scrollTop = term.scrollHeight; setTimeout(next, reduce ? 0 : 700); }, reduce ? 0 : 250); }
            })();
          }
          if (here.id === at) { type(); return; }
          var q = pos[at]; q.id = at;
          stop(here, q, me, function () { here = [q.x, q.y + 6]; here.id = at; type(); });
        })();
      });
    }
    /* a trail is not one rock: its panel replaces the detail, and the first rock on the route is where it starts */
    function openTrail(key) {
      var d = demos[key]; if (walking) resetView();
      rocks.forEach(function (g) { g.classList.remove('sel'); });
      detail.textContent = '';
      var chip = document.createElement('span'); chip.className = 'chip built'; chip.textContent = 'a trail'; detail.appendChild(chip);
      var h = document.createElement('h3'); h.textContent = d.route.join(' → '); h.className = 'trail-route'; detail.appendChild(h);
      var s = document.createElement('p'); s.textContent = d.summary || ''; detail.appendChild(s);
      demoUI(key, d.route[0]);
    }

    function select(id) {
      if (walking) resetView();
      rocks.forEach(function (g) { g.classList.toggle('sel', g.getAttribute('data-id') === id); });
      var p = pos[id].p;
      detail.textContent = '';
      var chip = document.createElement('span'); chip.className = 'chip ' + p.stage; chip.textContent = p.stage; detail.appendChild(chip);
      var h = document.createElement('h3'); h.textContent = p.name; detail.appendChild(h);
      var s = document.createElement('p'); s.textContent = p.summary; detail.appendChild(s);
      var dl = document.createElement('dl');
      function row(t, v) { if (!v) return; var dt = document.createElement('dt'); dt.textContent = t; var dd = document.createElement('dd'); dd.textContent = v; dl.appendChild(dt); dl.appendChild(dd); }
      row('Stage', data.stages[p.stage]); row('Authority', p.authority); row('Note', p.note);
      if (p.rests_on) row('Rests on', p.rests_on.join(', '));
      detail.appendChild(dl);
      if (demos[id]) demoUI(id, id); else { var nd = document.createElement('p'); nd.className = 'nodemo'; nd.textContent = 'No recorded session for this one yet.'; detail.appendChild(nd); }
      var links = document.createElement('div'); links.className = 'links';
      var a = document.createElement('a'); a.className = 'btn primary'; a.href = p.url; a.textContent = 'Repository'; links.appendChild(a);
      if (p.page) { var b = document.createElement('a'); b.className = 'btn ghost'; b.href = p.page; b.textContent = 'Landing page'; links.appendChild(b); }
      detail.appendChild(links);
    }
    select('cancho');

    var state = { kind: 'all', only: false };
    function apply() {
      rocks.forEach(function (g) {
        var p = pos[g.getAttribute('data-id')].p;
        var dim = (state.kind !== 'all' && p.kind !== state.kind) || (state.only && p.stage === 'design');
        g.classList.toggle('dim', dim);
        g.setAttribute('tabindex', dim ? -1 : 0);
      });
      restLines.forEach(function (l) {
        var dim = $('.rock[data-id="' + l.getAttribute('data-a') + '"]').classList.contains('dim') || $('.rock[data-id="' + l.getAttribute('data-b') + '"]').classList.contains('dim');
        l.classList.toggle('dim', dim);
      });
      svg.classList.toggle('filtered', state.kind !== 'all' || state.only);
    }
    var chips = $('#map-chips');
    [['all', 'All']].concat(Object.keys(data.kinds).map(function (k) { return [k, data.kinds[k]]; })).forEach(function (k, i) {
      var b = document.createElement('button'); b.type = 'button'; b.textContent = k[1]; b.setAttribute('aria-pressed', i === 0 ? 'true' : 'false'); b.setAttribute('data-k', k[0]);
      b.addEventListener('click', function () { state.kind = k[0]; chips.querySelectorAll('button[data-k]').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }); apply(); });
      chips.appendChild(b);
    });
    var only = document.createElement('button'); only.type = 'button'; only.textContent = 'Only what exists'; only.setAttribute('aria-pressed', 'false'); only.style.marginLeft = 'auto';
    only.addEventListener('click', function () { state.only = !state.only; only.setAttribute('aria-pressed', state.only ? 'true' : 'false'); apply(); });
    chips.appendChild(only);
    Object.keys(demos).filter(function (k) { return demos[k].route; }).forEach(function (k) {
      var b = document.createElement('button'); b.type = 'button'; b.className = 'trail-btn'; b.textContent = 'Trail: ' + demos[k].title; b.addEventListener('click', function () { openTrail(k); }); chips.insertBefore(b, only);
    });
    var counts = { built: 0, design: 0 };
    data.projects.forEach(function (p) { counts[p.stage === 'design' ? 'design' : 'built']++; });
    $('#map-count').textContent = counts.built + ' built, ' + counts.design + ' still on paper';
  }

  window.CanchoMap = { draw: draw };
})();
