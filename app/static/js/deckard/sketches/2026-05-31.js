// isolines — rings around a center that drifted while you watched.
window.__deckardSketch = function (ctx, w, h, rng, palette) {
  var P = {"fill": 0.842, "rings": 11, "k1": 6, "k2": 3, "warp": 0.071, "accentRate": 0.1, "alpha": 0.481, "wt": 0.961};
  var ground = palette[0], ink = palette[palette.length - 1], accent = palette[2] || ink;

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
};
