// rainfield — "What the Rain Keeps"
//
// A field of rain that mostly forgets, and a few drops it decides to hold.
// Deterministic given `rng`; reseeded per viewer and per refresh, so the wind
// and the kept drops are never quite the same reader to reader.
//
// Contract: return an optional step(t) for animation, or nothing for one frame.
window.__deckardSketch = function (ctx, w, h, rng, palette) {
  const [night, deep, teal, amber] = palette;
  const wind = (rng() - 0.5) * 0.6;
  const drops = [];
  const count = Math.floor((w * h) / 9000) + 60;

  for (let i = 0; i < count; i++) {
    drops.push({
      x: rng() * w,
      y: rng() * h,
      len: 8 + rng() * 22,
      spd: 2.5 + rng() * 5,
      kept: rng() < 0.04, // a few drops are remembered
      phase: rng() * Math.PI * 2,
    });
  }

  function backdrop() {
    ctx.fillStyle = night;
    ctx.fillRect(0, 0, w, h);
    const horizon = ctx.createLinearGradient(0, h * 0.55, 0, h);
    horizon.addColorStop(0, deep);
    horizon.addColorStop(1, night);
    ctx.fillStyle = horizon;
    ctx.fillRect(0, h * 0.55, w, h * 0.45);
  }

  return function step(t) {
    backdrop();
    ctx.lineCap = 'round';
    for (const d of drops) {
      d.y += d.spd;
      d.x += wind;
      if (d.y - d.len > h) {
        d.y = -d.len;
        d.x = rng() * w;
      }
      if (d.kept) {
        ctx.strokeStyle = amber;
        ctx.globalAlpha = 0.4 + 0.6 * Math.abs(Math.sin(t * 0.001 + d.phase));
        ctx.lineWidth = 1.6;
      } else {
        ctx.strokeStyle = teal;
        ctx.globalAlpha = 0.18 + (d.phase / (Math.PI * 2)) * 0.14;
        ctx.lineWidth = 1;
      }
      ctx.beginPath();
      ctx.moveTo(d.x, d.y);
      ctx.lineTo(d.x - wind * 3, d.y - d.len);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  };
};
