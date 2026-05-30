/* Deckard's Diary — in-browser IDE runtime.
 *
 * Loads the day's art sketch, runs it on a canvas with a per-viewer, per-refresh
 * seed, and shows the *exact same source it executed* in the code pane. The
 * sketch is plain first-party JS served from /static, so it loads via a normal
 * <script src> (no eval, no CSP relaxation). Source is fetched separately only
 * to display it — guaranteeing what you read is what ran.
 */
(function () {
  'use strict';

  var cfg = readConfig();
  if (!cfg) return;

  var canvas = document.getElementById('deckard-canvas');
  var ctx = canvas.getContext('2d');
  var seedLabel = document.getElementById('deckard-seed');
  var state = { seed: '', raf: 0, run: null, w: 0, h: 0, dpr: 1 };

  /* ---- seeding: persistent viewer token + per-refresh nonce ------------- */

  function viewerToken() {
    var key = 'deckard:viewer';
    var v = null;
    try {
      v = localStorage.getItem(key);
      if (!v) {
        var buf = new Uint32Array(2);
        (window.crypto || {}).getRandomValues
          ? window.crypto.getRandomValues(buf)
          : (buf[0] = (Math.random() * 4294967296) >>> 0);
        v = (buf[0] >>> 0).toString(36) + (buf[1] >>> 0).toString(36);
        localStorage.setItem(key, v);
      }
    } catch (e) {
      v = 'anon';
    }
    return v;
  }

  function freshNonce() {
    var n = (Math.random() * 4294967296) >>> 0;
    return n.toString(36);
  }

  // xmur3 string hash -> seeded mulberry32 PRNG. Deterministic per seed string.
  function makeRng(seed) {
    var h = 1779033703 ^ seed.length;
    for (var i = 0; i < seed.length; i++) {
      h = Math.imul(h ^ seed.charCodeAt(i), 3432918353);
      h = (h << 13) | (h >>> 19);
    }
    var a = (h ^= h >>> 16) >>> 0;
    return function () {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* ---- canvas sizing (device-pixel aware) ------------------------------ */

  function sizeCanvas() {
    var rect = canvas.getBoundingClientRect();
    var dpr = window.devicePixelRatio || 1;
    state.w = Math.max(1, Math.floor(rect.width));
    state.h = Math.max(1, Math.floor(rect.height));
    state.dpr = dpr;
    canvas.width = state.w * dpr;
    canvas.height = state.h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  /* ---- render: (re)build rng from the current seed, run the sketch ------ */

  function render() {
    if (state.raf) cancelAnimationFrame(state.raf);
    if (typeof window.__deckardSketch !== 'function') return;
    sizeCanvas();
    ctx.clearRect(0, 0, state.w, state.h);
    var rng = makeRng(state.seed);
    var step;
    try {
      step = window.__deckardSketch(ctx, state.w, state.h, rng, cfg.palette);
    } catch (e) {
      fail('the sketch could not run: ' + e.message);
      return;
    }
    if (typeof step === 'function') {
      var loop = function (t) {
        step(t);
        state.raf = requestAnimationFrame(loop);
      };
      state.raf = requestAnimationFrame(loop);
    }
    // static sketches (no returned step) have already drawn one frame.
  }

  function setSeed(seed) {
    state.seed = seed;
    if (seedLabel) seedLabel.textContent = seed;
  }

  function regenerate() {
    setSeed(cfg.viewer + ':' + freshNonce());
    render();
  }

  /* ---- code pane: fetch the exact source, light syntax highlight -------- */

  function paintSource() {
    var pane = document.getElementById('deckard-code');
    var gutter = document.getElementById('deckard-gutter');
    if (!pane) return;
    fetch(cfg.sketchUrl, { cache: 'no-cache' })
      .then(function (r) {
        return r.text();
      })
      .then(function (src) {
        pane.innerHTML = highlight(src);
        if (gutter) {
          var n = src.replace(/\n$/, '').split('\n').length;
          var rows = [];
          for (var i = 1; i <= n; i++) rows.push(i);
          gutter.textContent = rows.join('\n');
        }
      })
      .catch(function () {
        pane.textContent = '// source unavailable';
      });
  }

  var KEYWORDS = /\b(function|return|const|let|var|for|while|if|else|new|of|in|null|true|false|typeof|continue|break)\b/;
  var TOKEN = new RegExp(
    [
      '(\\/\\/[^\\n]*)', // 1 comment
      "('(?:\\\\.|[^'\\\\])*'|\"(?:\\\\.|[^\"\\\\])*\"|`(?:\\\\.|[^`\\\\])*`)", // 2 string
      KEYWORDS.source, // 3 keyword
      '(\\b\\d+\\.?\\d*\\b)', // 4 number
    ].join('|'),
    'g'
  );

  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function highlight(src) {
    return esc(src).replace(TOKEN, function (m, comment, str, kw, num) {
      if (comment) return '<span class="tok-comment">' + comment + '</span>';
      if (str) return '<span class="tok-string">' + str + '</span>';
      if (kw) return '<span class="tok-keyword">' + kw + '</span>';
      if (num) return '<span class="tok-number">' + num + '</span>';
      return m;
    });
  }

  function fail(msg) {
    var note = document.getElementById('deckard-note');
    if (note) note.textContent = msg;
  }

  /* ---- wiring ---------------------------------------------------------- */

  function debounce(fn, ms) {
    var id;
    return function () {
      clearTimeout(id);
      id = setTimeout(fn, ms);
    };
  }

  function boot() {
    cfg.viewer = viewerToken();
    setSeed(cfg.viewer + ':' + freshNonce());

    var regen = document.getElementById('deckard-regen');
    if (regen) regen.addEventListener('click', regenerate);

    var copy = document.getElementById('deckard-copy');
    if (copy)
      copy.addEventListener('click', function () {
        try {
          navigator.clipboard.writeText(state.seed);
          copy.textContent = 'copied';
          setTimeout(function () {
            copy.textContent = 'copy seed';
          }, 1200);
        } catch (e) {}
      });

    var save = document.getElementById('deckard-save');
    if (save)
      save.addEventListener('click', function () {
        try {
          var a = document.createElement('a');
          a.href = canvas.toDataURL('image/png');
          a.download = 'deckard-' + cfg.date + '.png';
          a.click();
        } catch (e) {}
      });

    window.addEventListener('resize', debounce(render, 180));

    // load the sketch, then render; show its source in parallel.
    paintSource();
    var s = document.createElement('script');
    s.src = cfg.sketchUrl;
    s.onload = render;
    s.onerror = function () {
      fail('the day’s sketch failed to load.');
    };
    document.body.appendChild(s);
  }

  function readConfig() {
    var el = document.getElementById('deckard-data');
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return null;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
