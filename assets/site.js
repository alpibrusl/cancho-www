/* cancho-www. No framework, no build step. Everything reads data/ecosystem.json, the same file agents get. */
(function () {
  'use strict';
  var R = window.Rocks, el = R.el;
  var reduced = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.documentElement.classList.add('js');
  var $ = function (s, c) { return (c || document).querySelector(s); };

  /* ---------- hero: boulders settle, the sun comes up ---------- */
  function hero() {
    var svg = $('#scene-svg');
    if (!svg) return;
    var r = R.rng(7);
    var L = function (k, cls) { return el('g', { class: 'layer', style: '--k:' + k }, svg); };
    var far = L(6);
    el('g', { class: 'sun-wrap' }, far).appendChild(el('circle', { cx: 330, cy: 235, r: 175, class: 'sun' }));
    R.ridge(L(10), r, 640, 600, 400, 70, 'ridge1');
    R.ridge(L(16), r, 640, 600, 450, 60, 'ridge2');
    var mid = L(24);
    var ground = el('path', { d: 'M-40,600 L-40,560 Q160,548 320,556 T680,552 L680,600Z', class: 'shrub' }, mid);
    ground.setAttribute('opacity', '.9');
    var fg = L(34);
    var order = [
      // seed, x, baseY, rx, ry, delay (bottom of the pile first)
      ['yelmo', 330, 560, 250, 205, 0.1, -3],
      ['left', 150, 448, 92, 66, 0.55, -8],
      ['right', 520, 486, 82, 58, 0.7, 7],
      ['top', 318, 262, 84, 66, 1.05, 9],
      ['cap', 332, 162, 40, 32, 1.35, -12],
      ['f1', 78, 566, 72, 46, 0.9, 6],
      ['f2', 540, 572, 88, 48, 0.8, -5],
      ['f3', 462, 578, 38, 26, 1.2, 10]
    ];
    order.forEach(function (o) {
      var holder = el('g', {}, fg);
      var inner = el('g', { class: 'drop', style: '--d:' + o[5] + 's;--r:' + o[6] + 'deg' }, holder);
      R.rock(inner, { seed: o[0], x: o[1], baseY: o[2], rx: o[3], ry: o[4], n: o[3] > 150 ? 16 : 12, jitter: o[3] > 150 ? 0.07 : 0.13, cracks: o[3] > 150 ? 4 : 2, lichen: o[3] > 150 ? 8 : 3 });
    });
    [[196, 566, 30], [40, 572, 24], [612, 566, 26], [440, 568, 18]].forEach(function (s, i) {
      var g = el('g', { class: 'drop', style: '--d:' + (1.5 + i * 0.1) + 's' }, fg);
      [[0, 0, 1], [-.7, 3, .8], [.7, 4, .75]].forEach(function (c) { el('circle', { cx: s[0] + c[0] * s[2], cy: s[1] - s[2] * .5 + c[1], r: s[2] * c[2], class: 'shrub' }, g); });
    });
    if (!reduced) {
      var box = $('.scene'), ticking = false;
      window.addEventListener('pointermove', function (e) {
        if (ticking) return; ticking = true;
        requestAnimationFrame(function () {
          ticking = false;
          var b = box.getBoundingClientRect();
          if (b.bottom < 0 || b.top > innerHeight) return;
          svg.style.setProperty('--px', ((e.clientX / innerWidth - 0.5) * -2).toFixed(3));
          svg.style.setProperty('--py', ((e.clientY / innerHeight - 0.5) * -2).toFixed(3));
        });
      }, { passive: true });
      svg.querySelectorAll('.layer').forEach(function (l) { l.style.setProperty('--px', 0); });
    }
  }

  /* ---------- cairn dividers ---------- */
  function cairns() {
    document.querySelectorAll('.cairn').forEach(function (c, n) {
      var svg = el('svg', { viewBox: '0 0 84 58', 'aria-hidden': 'true' }, c);
      [[42, 58, 32, 14, 3], [44, 38, 22, 11, 4], [41, 21, 13, 8, 5]].forEach(function (s, i) {
        var g = el('g', { class: 'st' }, svg);
        R.rock(g, { seed: 'cairn' + n + i, x: s[0], baseY: s[1], rx: s[2], ry: s[3], n: 9, cracks: 0, lichen: 0, jitter: 0.12 });
      });
    });
  }

  /* ---------- authority: split(world), release, and what the compiler refuses ---------- */
  function authority() {
    var host = $('#auth-svg');
    if (!host) return;
    var W = [400, 52];
    var row = { io: [130, 150], fs: [265, 150], ffi: [400, 150], heap: [535, 150], args: [670, 150] };
    var ground = { fs: [70, 282], ffi: [130, 282], heap: [190, 282], args: [250, 282], io: [310, 282] };
    var inBox = [700, 262];
    var names = ['io', 'fs', 'ffi', 'heap', 'args'];

    el('rect', { x: 28, y: 226, width: 330, height: 92, rx: 14, class: 'zone' }, host);
    el('text', { x: 44, y: 244, class: 'zlab' }, host).textContent = 'release(…)';
    var box = el('rect', { x: 520, y: 200, width: 252, height: 118, rx: 14, class: 'zone' }, host);
    var boxRow = el('text', { x: 536, y: 226, class: 'zrow' }, host);
    var boxLab = el('text', { x: 536, y: 304, class: 'zlab' }, host);
    boxLab.textContent = 'fn greet(io)';
    var worldLab = el('text', { x: 400, y: 100, class: 'zlab', 'text-anchor': 'middle' }, host);
    worldLab.textContent = 'World';
    
    names.forEach(function (n) {
      el('ellipse', { cx: row[n][0], cy: row[n][1] + 4, rx: 34, ry: 22, class: 'zone slot' }, host);
      el('text', { x: row[n][0], y: row[n][1] + 46, class: 'zlab slot', 'text-anchor': 'middle' }, host).textContent = n;
    });
    var caps = {};
    names.forEach(function (n, i) {
      var g = el('g', { class: 'cap-rock', style: '--x:' + W[0] + 'px;--y:' + W[1] + 'px;opacity:0' }, host);
      R.rock(g, { seed: 'cap-' + n, x: 0, baseY: 18, rx: n === 'io' ? 30 : 26, ry: 20, n: 10, cracks: 1, lichen: 1 });
      var lab = el('text', { x: 0, y: 40, class: 'lab' }, g);
      lab.textContent = n;
      caps[n] = g;
    });
    var world = el('g', { class: 'cap-rock', style: '--x:' + W[0] + 'px;--y:' + W[1] + 'px' }, host);
    R.rock(world, { seed: 'world', x: 0, baseY: 34, rx: 56, ry: 40, n: 13, cracks: 3, lichen: 4 });

    var scenarios = [
      {
        id: 'hand', label: 'Hand it down',
        code: ['let Split { io, fs, ffi, heap, args } = split(world);', 'release(fs); release(ffi); release(heap); release(args);', 'borrow mut io as &!i in { greet(i, "cancho"); }', 'release(io);'],
        greet: '[io_write]',
        steps: [
          { cap: 'main starts with one value: all the authority there is.', hl: -1, at: {}, vis: [] },
          { cap: 'split(world) hands it out once, as five separate values.', hl: 0, at: row, vis: names },
          { cap: 'Four are not needed here, so they are released. An unused capability is still a linear value.', hl: 1, at: { io: row.io, fs: ground.fs, ffi: ground.ffi, heap: ground.heap, args: ground.args }, vis: names },
          { cap: 'Only io is lent, and only to greet. greet’s signature says what it does with it.', hl: 2, at: { io: inBox, fs: ground.fs, ffi: ground.ffi, heap: ground.heap, args: ground.args }, vis: names, zone: 'on' },
          { cap: 'io is released too. Nothing is left over.', hl: 3, at: ground, vis: names, verdict: ['ok', 'compiles · performs io_write only'] }
        ]
      },
      {
        id: 'forget', label: 'Forget one',
        code: ['let Split { io, fs, ffi, heap, args } = split(world);', 'release(fs); release(ffi); release(args);', 'borrow mut io as &!i in { greet(i, "cancho"); }', 'release(io);'],
        greet: '[io_write]',
        steps: [
          { cap: 'Same program, one release(…) left out.', hl: -1, at: {}, vis: [] },
          { cap: 'split(world) hands out five values.', hl: 0, at: row, vis: names },
          { cap: 'fs, ffi and args are released. heap is not.', hl: 1, at: { io: row.io, fs: ground.fs, ffi: ground.ffi, heap: row.heap, args: ground.args }, vis: names, bad: ['heap'] },
          { cap: 'io is lent to greet as before.', hl: 2, at: { io: inBox, fs: ground.fs, ffi: ground.ffi, heap: row.heap, args: ground.args }, vis: names, bad: ['heap'], zone: 'on' },
          { cap: 'heap was never consumed. A leaked capability is a leaked power, so this is an error, not a warning.', hl: 3, hlBad: 1, at: { io: ground.io, fs: ground.fs, ffi: ground.ffi, heap: row.heap, args: ground.args }, vis: names, bad: ['heap'], verdict: ['bad', 'refused · linear-value-unconsumed'] }
        ]
      },
      {
        id: 'say', label: 'Do it without saying so',
        code: ['let Split { io, fs, ffi, heap, args } = split(world);', 'release(fs); release(ffi); release(heap); release(args);', 'fn greet(io: &!i Io) -> [] int { io.write_all(io, "hi") }', 'borrow mut io as &!i in { greet(i); }'],
        greet: '[]',
        steps: [
          { cap: 'This time greet’s signature claims it does nothing: its effect row is [].', hl: -1, at: {}, vis: [] },
          { cap: 'split(world), then the unused four are released.', hl: 1, at: { io: row.io, fs: ground.fs, ffi: ground.ffi, heap: ground.heap, args: ground.args }, vis: names },
          { cap: 'io is lent to greet, which writes with it.', hl: 3, at: { io: inBox, fs: ground.fs, ffi: ground.ffi, heap: ground.heap, args: ground.args }, vis: names, zone: 'bad' },
          { cap: 'Effect rows are exact: performing io_write without declaring it is refused. The row is not a comment.', hl: 2, hlBad: 2, at: { io: inBox, fs: ground.fs, ffi: ground.ffi, heap: ground.heap, args: ground.args }, vis: names, zone: 'bad', verdict: ['bad', 'refused · effect-not-declared'] }
        ]
      }
    ];

    var codeEl = $('#auth-code'), capEl = $('#auth-cap'), verdictEl = $('#auth-verdict'), dotsEl = $('#auth-dots');
    var cur = 0, step = 0, timer = null, playing = false;

    function render() {
      var sc = scenarios[cur], st = sc.steps[step];
      codeEl.querySelectorAll('.ln').forEach(function (l, i) { l.className = 'ln' + (i === st.hl ? ' on' : '') + (i === st.hlBad ? ' bad' : ''); if (st.hlBad === i) l.classList.remove('on'); });
      names.forEach(function (n) {
        var g = caps[n], shown = st.vis.indexOf(n) >= 0, p = shown ? (st.at[n] || row[n]) : W;
        g.style.setProperty('--x', p[0] + 'px'); g.style.setProperty('--y', p[1] + 'px');
        g.style.opacity = shown ? 1 : 0;
        g.classList.toggle('bad', !!(st.bad && st.bad.indexOf(n) >= 0));
        var small = p === ground[n] || p === inBox;
        g.style.transform = 'translate(' + p[0] + 'px,' + p[1] + 'px) scale(' + (shown ? (small ? 0.72 : 1) : 0.3) + ')';
      });
      worldLab.style.opacity = step === 0 ? 1 : 0;
      world.style.opacity = step === 0 ? 1 : 0;
      box.setAttribute('class', 'zone' + (st.zone ? ' ' + st.zone : ''));
      boxRow.textContent = sc.greet; boxLab.textContent = sc.id === 'say' ? 'greet(io) -> []' : 'greet(io)';
      capEl.textContent = st.cap;
      verdictEl.className = 'verdict' + (st.verdict ? ' ' + st.verdict[0] : '');
      verdictEl.textContent = st.verdict ? st.verdict[1] : '';
      dotsEl.querySelectorAll('i').forEach(function (d, i) { d.className = i <= step ? 'on' : ''; });
    }

    function load(i) {
      cur = i; step = 0;
      var sc = scenarios[i];
      codeEl.querySelectorAll('.ln').forEach(function (l, k) { l.textContent = sc.code[k] || ''; l.style.display = sc.code[k] ? '' : 'none'; });
      dotsEl.innerHTML = '';
      sc.steps.forEach(function () { dotsEl.appendChild(document.createElement('i')); });
      document.querySelectorAll('#auth-tabs button').forEach(function (b, k) { b.setAttribute('aria-pressed', k === i ? 'true' : 'false'); });
      render();
    }
    function next(manual) {
      var n = scenarios[cur].steps.length;
      if (step < n - 1) step++; else if (manual) step = 0; else { stop(); return; }
      render();
    }
    function prev() { var n = scenarios[cur].steps.length; step = (step - 1 + n) % n; render(); }
    function play() { if (playing) return; playing = true; $('#auth-play').textContent = '❚❚'; $('#auth-play').setAttribute('aria-label', 'Pause'); timer = setInterval(function () { next(false); }, 2600); }
    function stop() { playing = false; clearInterval(timer); $('#auth-play').textContent = '▶'; $('#auth-play').setAttribute('aria-label', 'Play'); }

    var tabs = $('#auth-tabs');
    scenarios.forEach(function (s, i) {
      var b = document.createElement('button'); b.textContent = s.label; b.type = 'button';
      b.addEventListener('click', function () { stop(); load(i); });
      tabs.appendChild(b);
    });
    $('#auth-next').addEventListener('click', function () { stop(); next(true); });
    $('#auth-prev').addEventListener('click', function () { stop(); prev(); });
    $('#auth-play').addEventListener('click', function () { playing ? stop() : play(); });
    load(0);
    if (!reduced && 'IntersectionObserver' in window) {
      var seen = false;
      new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          if (e.isIntersecting && !seen) { seen = true; setTimeout(function () { step = 0; render(); play(); next(false); }, 600); }
        });
      }, { threshold: 0.5 }).observe(host);
    }
  }

  /* ---------- the Pedriza map ---------- */
  function map(data) {
    var svg = $('#map-svg');
    if (!svg) return;
    var W = 1200, H = 800;
    var spots = {
      cancho: [260, 500], 'cancho-ui': [470, 650],
      'cancho-cache': [500, 250], 'cancho-hooks': [640, 330], 'cancho-gateway': [790, 250], 'cancho-mqtt': [930, 330], 'cancho-dns': [1060, 250], 'cancho-oci': [1120, 340],
      'cancho-schema': [520, 480], 'cancho-web': [690, 540], 'cancho-pg': [850, 480], 'cancho-log': [1000, 540], 'cancho-stats': [1100, 460], 'cancho-ml': [1110, 575],
      'cancho-tools': [600, 735], 'cancho-table': [770, 735], 'cancho-robot': [940, 735], 'cancho-gpu': [1090, 725]
    };
    var regions = [['language', 'La Pedriza', 80, 330], ['service', 'Services', 440, 150], ['library', 'Libraries', 440, 395], ['tool', 'Tools', 560, 628], ['edge', 'Edge', 900, 628]];
    var cg = el('g', {}, svg);
    for (var k = 0; k < 9; k++) {
      var rr = R.rng(100 + k), d = 'M0,' + (120 + k * 82);
      for (var x = 0; x <= W; x += 100) d += 'Q' + (x + 50) + ',' + (120 + k * 82 + (rr() - 0.5) * 80).toFixed(0) + ' ' + (x + 100) + ',' + (120 + k * 82 + (rr() - 0.5) * 40).toFixed(0);
      el('path', { d: d, class: 'contour' }, cg);
    }
    regions.forEach(function (r) { var t = el('text', { x: r[2], y: r[3], class: 'region' }, svg); t.textContent = r[1]; });
    var pos = {}, spare = 0;
    data.projects.forEach(function (p) {
      var big = p.id === 'cancho', s = spots[p.id] || [100 + (spare++) * 120, 770];
      pos[p.id] = { p: p, x: s[0], y: s[1], rx: big ? 118 : 46 + (R.hash(p.id) % 14), ry: big ? 88 : 34 + (R.hash(p.id + 'y') % 10) };
    });
    var lines = el('g', {}, svg), rocks = [];
    Object.keys(pos).sort(function (a, b) { return pos[a].y - pos[b].y; }).forEach(function (id) {
      var q = pos[id], p = q.p;
      var g = el('g', { class: 'rock ' + (p.stage === 'design' ? 'design' : 'built'), tabindex: 0, role: 'button', 'aria-label': p.name + ', ' + p.stage + ': ' + p.summary, 'data-id': id, 'data-kind': p.kind }, svg);
      var inner = el('g', { class: 'inner' }, g);
      R.rock(inner, { seed: p.id, x: q.x, baseY: q.y, rx: q.rx, ry: q.ry, n: p.id === 'cancho' ? 16 : 11, jitter: p.id === 'cancho' ? 0.07 : 0.14, cracks: p.id === 'cancho' ? 4 : 2, lichen: p.id === 'cancho' ? 7 : 2 });
      el('circle', { cx: q.x + q.rx * 0.55, cy: q.y - q.ry * 1.05, r: 6.5, class: 'pin ' + p.stage }, inner);
      el('text', { x: q.x, y: q.y + 19, class: 'name' }, g).textContent = p.name;
      g.addEventListener('click', function () { select(id); });
      g.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(id); } });
      rocks.push(g);
    });
    // "rests on" lines sit under the rocks
    svg.insertBefore(lines, rocks[0]);
    var restLines = [];
    data.projects.forEach(function (p) {
      (p.rests_on || []).forEach(function (t) {
        if (!pos[t]) return;
        var a = pos[p.id], b = pos[t];
        var path = el('path', { d: 'M' + a.x + ',' + (a.y - a.ry * 0.5) + 'Q' + ((a.x + b.x) / 2) + ',' + (Math.min(a.y, b.y) - 90) + ' ' + b.x + ',' + (b.y - b.ry * 0.5), class: 'rests', 'data-a': p.id, 'data-b': t }, lines);
        restLines.push(path);
      });
    });

    var detail = $('#detail');
    function select(id) {
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
      var links = document.createElement('div'); links.className = 'links';
      var a = document.createElement('a'); a.className = 'btn primary'; a.href = p.url; a.textContent = 'Repository'; links.appendChild(a);
      if (p.docs) { var b = document.createElement('a'); b.className = 'btn ghost'; b.href = p.docs; b.textContent = 'Docs'; links.appendChild(b); }
      detail.appendChild(links);
    }
    select('cancho');

    // filters
    var state = { kind: 'all', only: false };
    function apply() {
      rocks.forEach(function (g) {
        var id = g.getAttribute('data-id'), p = pos[id].p;
        var dim = (state.kind !== 'all' && p.kind !== state.kind) || (state.only && p.stage === 'design');
        g.classList.toggle('dim', dim);
        g.setAttribute('tabindex', dim ? -1 : 0);
      });
      restLines.forEach(function (l) {
        var dim = $('.rock[data-id="' + l.getAttribute('data-a') + '"]').classList.contains('dim') || $('.rock[data-id="' + l.getAttribute('data-b') + '"]').classList.contains('dim');
        l.classList.toggle('dim', dim);
      });
    }
    var chips = $('#map-chips');
    var kinds = [['all', 'All']].concat(Object.keys(data.kinds).map(function (k) { return [k, data.kinds[k]]; }));
    kinds.forEach(function (k, i) {
      var b = document.createElement('button'); b.type = 'button'; b.textContent = k[1]; b.setAttribute('aria-pressed', i === 0 ? 'true' : 'false');
      b.addEventListener('click', function () { state.kind = k[0]; chips.querySelectorAll('button[data-k]').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); }); apply(); });
      b.setAttribute('data-k', k[0]);
      chips.appendChild(b);
    });
    var only = document.createElement('button'); only.type = 'button'; only.textContent = 'Only what exists'; only.setAttribute('aria-pressed', 'false'); only.style.marginLeft = 'auto';
    only.addEventListener('click', function () { state.only = !state.only; only.setAttribute('aria-pressed', state.only ? 'true' : 'false'); apply(); });
    chips.appendChild(only);
    var counts = { built: 0, design: 0 };
    data.projects.forEach(function (p) { counts[p.stage === 'design' ? 'design' : 'built']++; });
    $('#map-count').textContent = counts.built + ' built, ' + counts.design + ' still on paper';
  }

  /* ---------- proof: waffles of the real numbers ---------- */
  function waffle(host, cols, total, passed, diffFrom) {
    var cell = 14, gap = 3, rows = Math.ceil(total / cols);
    var w = cols * (cell + gap) - gap, h = rows * (cell + gap) - gap;
    var svg = el('svg', { viewBox: '0 0 ' + w + ' ' + h, class: 'waffle', role: 'img', 'aria-label': passed + ' of ' + total }, host);
    for (var i = 0; i < total; i++) {
      var r = el('rect', { x: (i % cols) * (cell + gap), y: Math.floor(i / cols) * (cell + gap), width: cell, height: cell, rx: 3, style: '--i:' + i, 'data-pass': i < passed ? 1 : 0 }, svg);
      if (diffFrom != null && i >= diffFrom) r.setAttribute('class', 'diff');
    }
    return svg;
  }
  function proof(data) {
    var fig = {}; data.measured.figures.forEach(function (f) { fig[f.id] = f; });
    var items = [
      { id: 'conformance', cols: 44, diff: true }, { id: 'refusals', cols: 37 }
    ];
    items.forEach(function (it) {
      var f = fig[it.id], host = $('#w-' + it.id);
      if (!host) return;
      var s = waffle(host, it.cols, f.of, f.passed, it.diff ? f.passed : null);
      s.dataset.passed = f.passed;
    });
    var rules = $('#w-rules');
    if (rules) { var s = waffle(rules, 16, 62, 62); s.dataset.passed = 62; }
    $('#proof-date').textContent = data.measured.date + ', ' + data.measured.platform;
    document.querySelectorAll('[data-count]').forEach(function (b) { b.dataset.target = fig[b.dataset.count].passed || fig[b.dataset.count].value; });
  }
  function proofAnim() {
    var cards = document.querySelectorAll('.proof .card');
    if (!('IntersectionObserver' in window)) { cards.forEach(light); return; }
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { light(e.target); io.unobserve(e.target); } }); }, { threshold: 0.4 });
    cards.forEach(function (c) { io.observe(c); });
    function light(card) {
      card.querySelectorAll('.waffle rect').forEach(function (r) { if (r.getAttribute('data-pass') === '1' || r.classList.contains('diff')) r.classList.add('on'); });
      var b = card.querySelector('[data-count]');
      if (!b) return;
      var target = +b.dataset.target, n = b.querySelector('span');
      if (reduced) { n.textContent = target; return; }
      var t0 = performance.now();
      (function tick(t) { var k = Math.min(1, (t - t0) / 1300); n.textContent = Math.round(target * (1 - Math.pow(1 - k, 3))); if (k < 1) requestAnimationFrame(tick); })(t0);
    }
  }

  /* ---------- the not-here strike-throughs, reveal, cairns ---------- */
  function observers() {
    if (!('IntersectionObserver' in window)) { document.querySelectorAll('.reveal,.cairn,.nope').forEach(function (e) { e.classList.add('in'); }); return; }
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }); }, { threshold: 0.25 });
    document.querySelectorAll('.reveal,.cairn,.nope').forEach(function (e) { io.observe(e); });
  }

  /* ---------- agents: the same page, as data ---------- */
  function agents() {
    var cache = {};
    function load(name, into) {
      if (cache[name]) { into.textContent = cache[name]; return Promise.resolve(); }
      return fetch(name).then(function (r) { if (!r.ok) throw 0; return r.text(); }).then(function (t) { cache[name] = t; into.textContent = t; })
        .catch(function () { into.textContent = '# could not load ' + name + '\n# fetch it directly: ' + name; });
    }
    var human = $('#view-human'), agent = $('#view-agent'), full = $('#agent-full');
    function view(v) {
      document.body.setAttribute('data-view', v);
      human.setAttribute('aria-pressed', v === 'human'); agent.setAttribute('aria-pressed', v === 'agent');
      if (v === 'agent') { load('agents.md', full); scrollTo(0, 0); }
      try { history.replaceState(null, '', v === 'agent' ? '#agent' : location.pathname); } catch (e) { /* file:// */ }
    }
    human.addEventListener('click', function () { view('human'); });
    agent.addEventListener('click', function () { view('agent'); });
    if (location.hash === '#agent') view('agent');
  }

  var menu = $('.menu');
  if (menu) menu.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { menu.open = false; }); });
  hero(); cairns(); authority(); agents(); observers();
  fetch('data/ecosystem.json').then(function (r) { return r.json(); }).then(function (data) { map(data); proof(data); proofAnim(); })
    .catch(function () { var m = $('#map-fallback'); if (m) m.open = true; });
})();
