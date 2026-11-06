// rainfield — a field of weather that mostly forgets.
window.__deckardSketch = function (ctx, w, h, rng, palette) {
  const [night, deep, a, b] = palette;
  const wind = (rng() - 0.5) * 0.6;
  const drops = [];
  const count = Math.floor((w * h) / 9000) + 60;
  for (let i = 0; i < count; i++) {
    drops.push({ x: rng() * w, y: rng() * h, len: 8 + rng() * 22,
      spd: 2.5 + rng() * 5, kept: rng() < 0.05, phase: rng() * 6.28 });
  }
  return function step(t) {
    ctx.fillStyle = night; ctx.fillRect(0, 0, w, h);
    const g = ctx.createLinearGradient(0, h * 0.55, 0, h);
    g.addColorStop(0, deep); g.addColorStop(1, night);
    ctx.fillStyle = g; ctx.fillRect(0, h * 0.55, w, h * 0.45);
    ctx.lineCap = 'round';
    for (const d of drops) {
      d.y += d.spd; d.x += wind;
      if (d.y - d.len > h) { d.y = -d.len; d.x = rng() * w; }
      ctx.strokeStyle = d.kept ? b : a;
      ctx.globalAlpha = d.kept ? 0.4 + 0.6 * Math.abs(Math.sin(t * 0.001 + d.phase)) : 0.2;
      ctx.lineWidth = d.kept ? 1.6 : 1;
      ctx.beginPath(); ctx.moveTo(d.x, d.y); ctx.lineTo(d.x - wind * 3, d.y - d.len); ctx.stroke();
    }
    ctx.globalAlpha = 1;
  };
};
