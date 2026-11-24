// filings — small marks all turned by the same unseen weather.
window.__deckardSketch = function (ctx, w, h, rng, palette) {
  var P = {"margin": 0.126, "cols": 25, "freq": 0.007, "len": 0.789, "accentRate": 0.093, "alpha": 0.418, "wt": 1.084};
  var ground = palette[0], ink = palette[palette.length - 1], accent = palette[2] || ink;

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
};
