/* cancho-www. No framework, no build step. Everything reads data/ecosystem.json, the same file agents get. */
(function () {
  'use strict';
  var R = window.Rocks, el = R.el;
  var reduced = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.documentElement.classList.add('js');
  var $ = function (s, c) { return (c || document).querySelector(s); };

  /* ---------- hero: boulders settle, the sun comes up (the drawing is assets/scene.js) ---------- */
  function hero() {
    var svg = $('#scene-svg');
    if (!svg) return;
    window.Scene.draw(svg);
    if (reduced) return;
    var box = $('.scene'), ticking = false;
    svg.querySelectorAll('.layer').forEach(function (l) { l.style.setProperty('--px', 0); });
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
  function copyButtons() {
    document.querySelectorAll('.codebox[data-copy]').forEach(function (box) {
      var b = document.createElement('button'); b.type = 'button'; b.className = 'copy'; b.textContent = 'Copy'; b.setAttribute('aria-label', 'Copy the commands');
      b.addEventListener('click', function () {
        var text = box.querySelector('code').textContent.replace(/[ \t]+#.*$/gm, '').replace(/\s+$/gm, '');
        var done = function () { b.textContent = 'Copied'; setTimeout(function () { b.textContent = 'Copy'; }, 1500); };
        if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, function () { b.textContent = 'Select and copy'; });
        else { var r = document.createRange(); r.selectNodeContents(box.querySelector('code')); var s = getSelection(); s.removeAllRanges(); s.addRange(r); b.textContent = 'Press Ctrl+C'; }
      });
      box.appendChild(b);
    });
  }
  hero(); cairns(); authority(); agents(); observers(); copyButtons();
  Promise.all([fetch('data/ecosystem.json').then(function (r) { return r.json(); }), fetch('data/demos.json').then(function (r) { return r.json(); }).catch(function () { return {}; })]).then(function (rs) { var data = rs[0]; window.CanchoMap.draw(data, rs[1]); proof(data); proofAnim(); })
    .catch(function () { var m = $('#map-fallback'); if (m) m.open = true; });
})();
