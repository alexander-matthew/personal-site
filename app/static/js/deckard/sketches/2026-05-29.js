// hatching — shading where the light leaned; nothing more.
window.__deckardSketch = function (ctx, w, h, rng, palette) {
  var P = {"angle": 0.275, "spacing": 11, "bands": 2, "accN": 11, "alpha": 0.42, "wt": 0.629};
  var ground = palette[0], ink = palette[palette.length - 1], accent = palette[2] || ink;

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
};
