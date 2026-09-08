// driftfield — particles pulled along a field that never settles the same twice.
window.__deckardSketch = function (ctx, w, h, rng, palette) {
  const [night, , a, b, c] = palette;
  const cols = [a, b, c];
  const ph = [rng() * 6.28, rng() * 6.28, rng() * 6.28];
  const pts = [];
  for (let i = 0; i < 700; i++)
    pts.push({ x: rng() * w, y: rng() * h, c: cols[(rng() * cols.length) | 0] });
  function ang(x, y) {
    return (Math.sin(x * 0.006 + ph[0]) + Math.cos(y * 0.008 + ph[1]) +
      Math.sin((x + y) * 0.004 + ph[2])) * 2.2;
  }
  ctx.fillStyle = night; ctx.fillRect(0, 0, w, h);
  return function step() {
    ctx.globalAlpha = 0.04; ctx.fillStyle = night; ctx.fillRect(0, 0, w, h);
    ctx.globalAlpha = 0.5;
    for (const p of pts) {
      const a2 = ang(p.x, p.y);
      const nx = p.x + Math.cos(a2) * 1.2, ny = p.y + Math.sin(a2) * 1.2;
      ctx.strokeStyle = p.c; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(nx, ny); ctx.stroke();
      p.x = nx; p.y = ny;
      if (p.x < 0 || p.x > w || p.y < 0 || p.y > h) { p.x = rng() * w; p.y = rng() * h; }
    }
    ctx.globalAlpha = 1;
  };
};
