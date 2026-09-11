// dissolving grid — a grid keeping its composure, then losing it toward one corner.
window.__deckardSketch = function (ctx, w, h, rng, palette) {
  var P = {"n": 12, "fill": 0.806, "size": 0.651, "chaos": 2.435, "shift": 0.732, "accentRate": 0.069, "alpha": 0.6, "wt": 0.878};
  var ground = palette[0], ink = palette[palette.length - 1], accent = palette[2] || ink;

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
};
