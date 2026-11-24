"""A library of distinct generative-art *systems* for Deckard's Diary.

The old generator had one fixed sketch per form, so every entry of a given form
ran identical JS and only the palette changed — reskinning, not variation. This
module instead holds many independent systems (Truchet weaves, flow fields,
Molnar grids, harmonographs, circle packings, …). ``compose_sketch`` picks one
per entry from the date-seeded rng and *bakes that day's randomized parameters*
into the emitted JS, so consecutive pages are structurally different algorithms,
not the same code recolored. The runtime rng/palette still add per-viewer,
per-refresh variation on top.

Each emitted sketch obeys the runtime contract: it defines
``window.__deckardSketch(ctx, w, h, rng, palette)``; returning an optional
``step(t)`` for animation. We bake params as a ``var P = {...}`` literal and add
an ink/accent prelude, so each system body just reads ``P`` and draws.

Style: minimalist, traditional generative / plotter-style line work — controlled
randomness, generous negative space, thin strokes, one sparing accent. No
photo-real simulation.
"""
from __future__ import annotations

import json


def _r(x: float) -> float:
    return round(x, 3)


# --- system bodies ---------------------------------------------------------
# Each body is the *inside* of window.__deckardSketch. Available in scope:
#   ctx, w, h, rng, palette, P, ground, ink, accent
# Body must end by returning a step() function (or drawing a static frame).

BODY_TRUCHET_ARCS = """
  var n = P.n, span = Math.min(w, h) * P.fill, cell = span / n;
  var ox = (w - span) / 2, oy = (h - span) / 2;
  var tiles = [];
  for (var i = 0; i < n; i++) for (var j = 0; j < n; j++)
    tiles.push({ i: i, j: j, k: rng() < 0.5 ? 0 : 1, rare: rng() < P.accentRate,
      jx: (rng() - 0.5) * cell * P.jit, jy: (rng() - 0.5) * cell * P.jit });
  ctx.fillStyle = ground; ctx.fillRect(0, 0, w, h); ctx.lineCap = 'round';
  var d = 0;
  return function () {
    var t = Math.min(tiles.length, d + P.speed);
    for (; d < t; d++) {
      var T = tiles[d], x = ox + T.i * cell + T.jx, y = oy + T.j * cell + T.jy, r = cell / 2;
      ctx.strokeStyle = T.rare ? accent : ink;
      ctx.globalAlpha = T.rare ? 0.85 : P.alpha;
      ctx.lineWidth = T.rare ? P.wt + 0.5 : P.wt;
      if (T.k === 0) {
        ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI / 2); ctx.stroke();
        ctx.beginPath(); ctx.arc(x + cell, y + cell, r, Math.PI, Math.PI * 1.5); ctx.stroke();
      } else {
        ctx.beginPath(); ctx.arc(x + cell, y, r, Math.PI / 2, Math.PI); ctx.stroke();
        ctx.beginPath(); ctx.arc(x, y + cell, r, Math.PI * 1.5, Math.PI * 2); ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;
  };
"""

BODY_TRUCHET_LINES = """
  var n = P.n, span = Math.min(w, h) * P.fill, cell = span / n;
  var ox = (w - span) / 2, oy = (h - span) / 2;
  var cs = [];
  for (var i = 0; i < n; i++) for (var j = 0; j < n; j++)
    cs.push({ i: i, j: j, k: rng() < 0.5, rare: rng() < P.accentRate });
  ctx.fillStyle = ground; ctx.fillRect(0, 0, w, h); ctx.lineCap = 'round';
  var d = 0;
  return function () {
    var t = Math.min(cs.length, d + P.speed);
    for (; d < t; d++) {
      var C = cs[d], x = ox + C.i * cell, y = oy + C.j * cell;
      ctx.strokeStyle = C.rare ? accent : ink;
      ctx.globalAlpha = C.rare ? 0.85 : P.alpha;
      ctx.lineWidth = P.wt;
      ctx.beginPath();
      if (C.k) { ctx.moveTo(x, y); ctx.lineTo(x + cell, y + cell); }
      else { ctx.moveTo(x + cell, y); ctx.lineTo(x, y + cell); }
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  };
"""

BODY_FLOW = """
  var m = Math.min(w, h) * P.margin, f = P.freq, ph = [rng() * 6.28, rng() * 6.28, rng() * 6.28];
  function ang(x, y) {
    return (Math.sin(x * f + ph[0]) + Math.cos(y * f * 1.3 + ph[1]) + Math.sin((x + y) * f * 0.7 + ph[2])) * Math.PI;
  }
  ctx.fillStyle = ground; ctx.fillRect(0, 0, w, h); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  var L = [];
  for (var i = 0; i < P.count; i++)
    L.push({ x: m + rng() * (w - 2 * m), y: m + rng() * (h - 2 * m), rare: rng() < P.accentRate, len: P.len * (0.5 + rng()) });
  var li = 0;
  return function () {
    if (li >= L.length) return;
    var s = L[li];
    ctx.strokeStyle = s.rare ? accent : ink;
    ctx.globalAlpha = s.rare ? 0.8 : P.alpha;
    ctx.lineWidth = s.rare ? P.wt + 0.4 : P.wt;
    ctx.beginPath();
    var x = s.x, y = s.y; ctx.moveTo(x, y);
    for (var k = 0; k < s.len; k++) {
      var a = ang(x, y); x += Math.cos(a) * P.step; y += Math.sin(a) * P.step;
      if (x < m || x > w - m || y < m || y > h - m) break;
      ctx.lineTo(x, y);
    }
    ctx.stroke(); ctx.globalAlpha = 1; li++;
  };
"""

BODY_MOLNAR = """
  var n = P.n, span = Math.min(w, h) * P.fill, cell = span / n;
  var ox = (w - span) / 2, oy = (h - span) / 2, s = cell * P.size;
  var cx = rng() < 0.5 ? 0 : n - 1, cy = rng() < 0.5 ? 0 : n - 1;
  var cs = [];
  for (var i = 0; i < n; i++) for (var j = 0; j < n; j++) {
    var dis = Math.hypot(i - cx, j - cy) / (n * 1.414);
    cs.push({ i: i, j: j, acc: rng() < P.accentRate, rot: (rng() - 0.5) * dis * dis * P.chaos,
      jx: (rng() - 0.5) * dis * cell * P.shift, jy: (rng() - 0.5) * dis * cell * P.shift });
  }
  ctx.fillStyle = ground; ctx.fillRect(0, 0, w, h);
  var d = 0;
  return function () {
    var t = Math.min(cs.length, d + 4);
    for (; d < t; d++) {
      var C = cs[d], px = ox + C.i * cell + cell / 2 + C.jx, py = oy + C.j * cell + cell / 2 + C.jy;
      ctx.save(); ctx.translate(px, py); ctx.rotate(C.rot);
      ctx.strokeStyle = C.acc ? accent : ink; ctx.globalAlpha = C.acc ? 0.9 : P.alpha; ctx.lineWidth = P.wt;
      ctx.strokeRect(-s / 2, -s / 2, s, s); ctx.restore();
    }
    ctx.globalAlpha = 1;
  };
"""

BODY_FILINGS = """
  var m = Math.min(w, h) * P.margin, gx = P.cols, gy = Math.max(2, Math.round(P.cols * h / w)), f = P.freq, ph = rng() * 6.28;
  var cw = (w - 2 * m) / gx, ch = (h - 2 * m) / gy, len = Math.min(cw, ch) * P.len;
  function ang(x, y) { return (Math.sin(x * f + ph) + Math.cos(y * f * 1.2)) * Math.PI; }
  ctx.fillStyle = ground; ctx.fillRect(0, 0, w, h); ctx.lineCap = 'round';
  var pts = [];
  for (var i = 0; i < gx; i++) for (var j = 0; j < gy; j++) pts.push([m + cw * (i + 0.5), m + ch * (j + 0.5), rng() < P.accentRate]);
  var d = 0;
  return function () {
    var t = Math.min(pts.length, d + 8);
    for (; d < t; d++) {
      var p = pts[d], a = ang(p[0], p[1]);
      ctx.strokeStyle = p[2] ? accent : ink; ctx.globalAlpha = p[2] ? 0.85 : P.alpha; ctx.lineWidth = P.wt;
      ctx.beginPath();
      ctx.moveTo(p[0] - Math.cos(a) * len / 2, p[1] - Math.sin(a) * len / 2);
      ctx.lineTo(p[0] + Math.cos(a) * len / 2, p[1] + Math.sin(a) * len / 2);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  };
"""

BODY_RIDGE = """
  var m = Math.min(w, h) * P.margin, left = m, right = w - m, span = right - left, top = m, bottom = h - m, rows = P.rows;
  var amp = (bottom - top) / rows * P.amp, sd = [];
  for (var r = 0; r < rows; r++) sd.push([rng() * 10, rng() * 10, rng() * 10, rng() < P.accentRate]);
  function rg(r, u) {
    var s = sd[r];
    return Math.sin(u * 6.28 * 1.3 + s[0]) * 0.5 + Math.sin(u * 6.28 * 2.7 + s[1]) * 0.3 + Math.sin(u * 6.28 * 4.9 + s[2]) * 0.2;
  }
  ctx.fillStyle = ground; ctx.fillRect(0, 0, w, h); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  var row = 0;
  return function () {
    if (row >= rows) return;
    var by = top + (bottom - top) * (row / (rows - 1)), s = sd[row];
    ctx.strokeStyle = s[3] ? accent : ink;
    ctx.globalAlpha = s[3] ? 0.85 : 0.3 + 0.5 * (row / rows);
    ctx.lineWidth = s[3] ? 1.4 : P.wt;
    ctx.beginPath();
    for (var x = 0; x <= span; x += 3) {
      var u = x / span, env = Math.sin(Math.PI * u), y = by - rg(row, u) * amp * env;
      x === 0 ? ctx.moveTo(left + x, y) : ctx.lineTo(left + x, y);
    }
    ctx.stroke(); ctx.globalAlpha = 1; row++;
  };
"""

BODY_ISOLINES = """
  var cx = w / 2 + (rng() - 0.5) * w * 0.2, cy = h / 2 + (rng() - 0.5) * h * 0.2;
  var R = Math.min(w, h) * P.fill / 2, rings = P.rings, ph = [rng() * 6.28, rng() * 6.28];
  ctx.fillStyle = ground; ctx.fillRect(0, 0, w, h); ctx.lineJoin = 'round';
  var ri = 0;
  return function () {
    if (ri >= rings) return;
    var rad = R * (ri + 1) / rings, acc = rng() < P.accentRate;
    ctx.strokeStyle = acc ? accent : ink; ctx.globalAlpha = acc ? 0.85 : P.alpha; ctx.lineWidth = acc ? P.wt + 0.3 : P.wt;
    ctx.beginPath();
    for (var a = 0; a <= 6.2832; a += 0.06) {
      var dd = rad + Math.sin(a * P.k1 + ph[0]) * P.warp * rad + Math.sin(a * P.k2 + ph[1]) * P.warp * rad * 0.5;
      var x = cx + Math.cos(a) * dd, y = cy + Math.sin(a) * dd;
      a === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath(); ctx.stroke(); ctx.globalAlpha = 1; ri++;
  };
"""

BODY_SUBDIVISION = """
  var m = Math.min(w, h) * P.margin;
  ctx.fillStyle = ground; ctx.fillRect(0, 0, w, h);
  var rects = [];
  (function sub(x, y, ww, hh, depth) {
    if (depth <= 0 || (ww < P.minSize && hh < P.minSize) || rng() > P.split) { rects.push([x, y, ww, hh, rng() < P.accentRate]); return; }
    if (ww > hh) { var c = ww * (0.3 + rng() * 0.4); sub(x, y, c, hh, depth - 1); sub(x + c, y, ww - c, hh, depth - 1); }
    else { var c2 = hh * (0.3 + rng() * 0.4); sub(x, y, ww, c2, depth - 1); sub(x, y + c2, ww, hh - c2, depth - 1); }
  })(m, m, w - 2 * m, h - 2 * m, P.depth);
  var d = 0;
  return function () {
    var t = Math.min(rects.length, d + 3);
    for (; d < t; d++) {
      var R = rects[d];
      ctx.strokeStyle = R[4] ? accent : ink; ctx.globalAlpha = R[4] ? 0.9 : P.alpha; ctx.lineWidth = P.wt;
      ctx.strokeRect(R[0] + P.pad, R[1] + P.pad, R[2] - 2 * P.pad, R[3] - 2 * P.pad);
    }
    ctx.globalAlpha = 1;
  };
"""

BODY_PACKING = """
  var m = Math.min(w, h) * P.margin;
  ctx.fillStyle = ground; ctx.fillRect(0, 0, w, h);
  var circ = [], rmin = P.rmin, rmax = P.rmax;
  for (var a = 0; a < P.tries; a++) {
    var x = m + rng() * (w - 2 * m), y = m + rng() * (h - 2 * m), r = rmin + rng() * (rmax - rmin), ok = true;
    for (var b = 0; b < circ.length; b++) {
      var c = circ[b], dd = Math.hypot(x - c[0], y - c[1]);
      if (dd < r + c[2] + P.gap) { r = dd - c[2] - P.gap; if (r < rmin) { ok = false; break; } }
    }
    if (ok && r >= rmin) circ.push([x, y, r, rng() < P.accentRate]);
  }
  var d = 0;
  return function () {
    var t = Math.min(circ.length, d + 4);
    for (; d < t; d++) {
      var C = circ[d];
      ctx.strokeStyle = C[3] ? accent : ink; ctx.globalAlpha = C[3] ? 0.9 : P.alpha; ctx.lineWidth = P.wt;
      ctx.beginPath(); ctx.arc(C[0], C[1], C[2], 0, 6.2832); ctx.stroke();
    }
    ctx.globalAlpha = 1;
  };
"""

BODY_HATCH = """
  var aa = P.angle, sp = P.spacing, ph = rng() * 6.28;
  ctx.fillStyle = ground; ctx.fillRect(0, 0, w, h); ctx.lineCap = 'round';
  var dx = Math.cos(aa), dy = Math.sin(aa), nx = -dy, ny = dx, diag = Math.hypot(w, h);
  var lines = [];
  for (var t = -diag; t < diag; t += sp) lines.push(t);
  var d = 0;
  return function () {
    var e = Math.min(lines.length, d + 3);
    for (; d < e; d++) {
      var t = lines[d], cxp = w / 2 + nx * t, cyp = h / 2 + ny * t, u = (t + diag) / (2 * diag);
      var dens = 0.25 + 0.75 * Math.abs(Math.sin(u * 6.28 * P.bands + ph));
      ctx.globalAlpha = dens * P.alpha;
      ctx.strokeStyle = (d % P.accN === 0) ? accent : ink;
      ctx.lineWidth = P.wt;
      ctx.beginPath(); ctx.moveTo(cxp - dx * diag, cyp - dy * diag); ctx.lineTo(cxp + dx * diag, cyp + dy * diag); ctx.stroke();
    }
    ctx.globalAlpha = 1;
  };
"""

BODY_WALKERS = """
  var m = Math.min(w, h) * P.margin, ws = [];
  for (var i = 0; i < P.count; i++)
    ws.push({ x: m + rng() * (w - 2 * m), y: m + rng() * (h - 2 * m), a: rng() * 6.28, rare: rng() < P.accentRate, life: P.life });
  ctx.fillStyle = ground; ctx.fillRect(0, 0, w, h); ctx.lineCap = 'round';
  return function () {
    for (var i = 0; i < ws.length; i++) {
      var W = ws[i]; if (W.life <= 0) continue;
      var nxp = W.x + Math.cos(W.a) * P.step, nyp = W.y + Math.sin(W.a) * P.step;
      ctx.strokeStyle = W.rare ? accent : ink; ctx.globalAlpha = P.alpha; ctx.lineWidth = P.wt;
      ctx.beginPath(); ctx.moveTo(W.x, W.y); ctx.lineTo(nxp, nyp); ctx.stroke();
      W.x = nxp; W.y = nyp; W.a += (rng() - 0.5) * P.turn; W.life--;
      if (W.x < m || W.x > w - m || W.y < m || W.y > h - m) W.a += Math.PI;
    }
    ctx.globalAlpha = 1;
  };
"""

BODY_HARMONOGRAPH = """
  var cx = w / 2, cy = h / 2, R = Math.min(w, h) * P.fill / 2;
  var p1 = rng() * 6.28, p2 = rng() * 6.28;
  ctx.fillStyle = ground; ctx.fillRect(0, 0, w, h); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  ctx.strokeStyle = ink; ctx.globalAlpha = P.alpha; ctx.lineWidth = P.wt;
  var tt = 0;
  return function () {
    if (tt >= P.maxT) return;
    ctx.beginPath();
    var started = false, end = Math.min(P.maxT, tt + P.seg);
    for (; tt <= end; tt += 0.02) {
      var dec = Math.exp(-P.decay * tt);
      var x = cx + R * dec * Math.sin(P.a1 * tt + p1) * Math.cos(P.b1 * tt);
      var y = cy + R * dec * Math.sin(P.a2 * tt + p2) * Math.cos(P.b2 * tt);
      started ? ctx.lineTo(x, y) : ctx.moveTo(x, y); started = true;
    }
    ctx.stroke();
  };
"""


# --- registry --------------------------------------------------------------
# key/title (display), a colophon (shown on the page — keep wabi-sabi and free of
# any forbidden term), a params(rng)->dict sampler, and the JS body.

SYSTEMS = [
    {
        'key': 'arc-weave', 'title': 'arc weave',
        'colophon': 'arc tiles that almost agree; a few the hand let wander.',
        'body': BODY_TRUCHET_ARCS,
        'params': lambda rng: {
            'n': rng.randint(7, 16), 'fill': _r(rng.uniform(0.72, 0.86)),
            'accentRate': _r(rng.uniform(0.04, 0.12)), 'jit': _r(rng.uniform(0, 0.12)),
            'speed': rng.randint(2, 6), 'alpha': _r(rng.uniform(0.4, 0.6)), 'wt': _r(rng.uniform(0.8, 1.5)),
        },
    },
    {
        'key': 'diagonal-weave', 'title': 'diagonal weave',
        'colophon': 'a weave of diagonals; a maze with no inside.',
        'body': BODY_TRUCHET_LINES,
        'params': lambda rng: {
            'n': rng.randint(9, 22), 'fill': _r(rng.uniform(0.74, 0.88)),
            'accentRate': _r(rng.uniform(0.04, 0.1)), 'speed': rng.randint(3, 8),
            'alpha': _r(rng.uniform(0.4, 0.6)), 'wt': _r(rng.uniform(0.8, 1.4)),
        },
    },
    {
        'key': 'streamlines', 'title': 'streamlines',
        'colophon': 'lines following a current you cannot see.',
        'body': BODY_FLOW,
        'params': lambda rng: {
            'margin': _r(rng.uniform(0.07, 0.13)), 'freq': _r(rng.uniform(0.004, 0.013)),
            'count': rng.randint(40, 140), 'len': rng.randint(40, 160), 'step': _r(rng.uniform(2, 3.5)),
            'accentRate': _r(rng.uniform(0.04, 0.1)), 'alpha': _r(rng.uniform(0.3, 0.5)), 'wt': _r(rng.uniform(0.6, 1.1)),
        },
    },
    {
        'key': 'dissolving-grid', 'title': 'dissolving grid',
        'colophon': 'a grid keeping its composure, then losing it toward one corner.',
        'body': BODY_MOLNAR,
        'params': lambda rng: {
            'n': rng.randint(8, 16), 'fill': _r(rng.uniform(0.72, 0.86)), 'size': _r(rng.uniform(0.5, 0.7)),
            'chaos': _r(rng.uniform(2, 4)), 'shift': _r(rng.uniform(0.4, 0.8)),
            'accentRate': _r(rng.uniform(0.03, 0.08)), 'alpha': _r(rng.uniform(0.45, 0.6)), 'wt': _r(rng.uniform(0.8, 1.2)),
        },
    },
    {
        'key': 'filings', 'title': 'filings',
        'colophon': 'small marks all turned by the same unseen weather.',
        'body': BODY_FILINGS,
        'params': lambda rng: {
            'margin': _r(rng.uniform(0.08, 0.13)), 'cols': rng.randint(14, 30), 'freq': _r(rng.uniform(0.005, 0.015)),
            'len': _r(rng.uniform(0.7, 1.4)), 'accentRate': _r(rng.uniform(0.04, 0.1)),
            'alpha': _r(rng.uniform(0.35, 0.55)), 'wt': _r(rng.uniform(0.7, 1.1)),
        },
    },
    {
        'key': 'ridgelines', 'title': 'ridgelines',
        'colophon': 'one horizon, read many times; a line that will not settle.',
        'body': BODY_RIDGE,
        'params': lambda rng: {
            'margin': _r(rng.uniform(0.1, 0.16)), 'rows': rng.randint(14, 30), 'amp': _r(rng.uniform(1.8, 3.2)),
            'accentRate': _r(rng.uniform(0.06, 0.14)), 'wt': _r(rng.uniform(0.8, 1.0)),
        },
    },
    {
        'key': 'isolines', 'title': 'isolines',
        'colophon': 'rings around a center that drifted while you watched.',
        'body': BODY_ISOLINES,
        'params': lambda rng: {
            'fill': _r(rng.uniform(0.7, 0.92)), 'rings': rng.randint(10, 26),
            'k1': rng.randint(2, 6), 'k2': rng.randint(3, 9), 'warp': _r(rng.uniform(0.02, 0.09)),
            'accentRate': _r(rng.uniform(0.06, 0.12)), 'alpha': _r(rng.uniform(0.35, 0.55)), 'wt': _r(rng.uniform(0.7, 1.1)),
        },
    },
    {
        'key': 'subdivision', 'title': 'subdivision',
        'colophon': 'a page dividing itself until it forgets why.',
        'body': BODY_SUBDIVISION,
        'params': lambda rng: {
            'margin': _r(rng.uniform(0.08, 0.13)), 'depth': rng.randint(5, 9), 'split': _r(rng.uniform(0.6, 0.85)),
            'minSize': rng.randint(18, 40), 'pad': rng.randint(2, 6),
            'accentRate': _r(rng.uniform(0.05, 0.1)), 'alpha': _r(rng.uniform(0.4, 0.6)), 'wt': _r(rng.uniform(0.8, 1.2)),
        },
    },
    {
        'key': 'packing', 'title': 'packing',
        'colophon': 'rooms filling a space, none quite touching.',
        'body': BODY_PACKING,
        'params': lambda rng: {
            'margin': _r(rng.uniform(0.07, 0.12)), 'tries': rng.randint(150, 400),
            'rmin': rng.randint(6, 12), 'rmax': rng.randint(30, 70), 'gap': rng.randint(2, 6),
            'accentRate': _r(rng.uniform(0.05, 0.1)), 'alpha': _r(rng.uniform(0.4, 0.6)), 'wt': _r(rng.uniform(0.7, 1.1)),
        },
    },
    {
        'key': 'hatching', 'title': 'hatching',
        'colophon': 'shading where the light leaned; nothing more.',
        'body': BODY_HATCH,
        'params': lambda rng: {
            'angle': _r(rng.uniform(0, 3.14)), 'spacing': rng.randint(7, 16), 'bands': rng.randint(1, 4),
            'accN': rng.randint(7, 15), 'alpha': _r(rng.uniform(0.25, 0.45)), 'wt': _r(rng.uniform(0.6, 1.0)),
        },
    },
    {
        'key': 'walkers', 'title': 'walkers',
        'colophon': 'a few pens let loose, each sure of a different north.',
        'body': BODY_WALKERS,
        'params': lambda rng: {
            'margin': _r(rng.uniform(0.06, 0.12)), 'count': rng.randint(3, 9), 'life': rng.randint(300, 900),
            'step': _r(rng.uniform(1.5, 3)), 'turn': _r(rng.uniform(0.3, 0.9)),
            'accentRate': _r(rng.uniform(0.1, 0.3)), 'alpha': _r(rng.uniform(0.25, 0.45)), 'wt': _r(rng.uniform(0.7, 1.2)),
        },
    },
    {
        'key': 'harmonograph', 'title': 'harmonograph',
        'colophon': "a pendulum's long sentence, winding down.",
        'body': BODY_HARMONOGRAPH,
        'params': lambda rng: {
            'fill': _r(rng.uniform(0.7, 0.95)), 'a1': rng.randint(1, 5), 'a2': rng.randint(1, 5),
            'b1': _r(rng.uniform(0.5, 4)), 'b2': _r(rng.uniform(0.5, 4)), 'decay': _r(rng.uniform(0.003, 0.02)),
            'maxT': rng.randint(40, 120), 'seg': rng.randint(4, 10),
            'alpha': _r(rng.uniform(0.5, 0.8)), 'wt': _r(rng.uniform(0.6, 1.0)),
        },
    },
]


def compose_sketch(rng) -> tuple[str, str, str]:
    """Pick a system from the (date-seeded) rng, bake its params, emit the JS.

    Returns (sketch_js, art_title, colophon).
    """
    sys = rng.choice(SYSTEMS)
    params = sys['params'](rng)
    js = (
        f"// {sys['title']} — {sys['colophon']}\n"
        "window.__deckardSketch = function (ctx, w, h, rng, palette) {\n"
        "  var P = " + json.dumps(params) + ";\n"
        "  var ground = palette[0], ink = palette[palette.length - 1], accent = palette[2] || ink;\n"
        + sys['body'].rstrip("\n") + "\n};\n"
    )
    return js, sys['title'], sys['colophon']
