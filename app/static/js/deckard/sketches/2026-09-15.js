// nightwatch — a skyline that blinks back; a city that never was.
window.__deckardSketch = function (ctx, w, h, rng, palette) {
  const [night, deep, red, cyan, bone] = palette;
  const towers = [];
  let x = -20;
  while (x < w + 20) {
    const tw = 22 + rng() * 60, th = h * (0.25 + rng() * 0.55);
    const cols = Math.max(1, Math.floor(tw / 10)), rows = Math.floor(th / 12), wins = [];
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++)
      if (rng() < 0.55) wins.push({ c, r, lit: rng(), flick: rng() });
    towers.push({ x, tw, th, cols, wins, beacon: rng() * 6.28 });
    x += tw + 4 + rng() * 10;
  }
  return function step(t) {
    ctx.fillStyle = night; ctx.fillRect(0, 0, w, h);
    const g = ctx.createLinearGradient(0, h, 0, h * 0.3);
    g.addColorStop(0, deep); g.addColorStop(1, night);
    ctx.fillStyle = g; ctx.fillRect(0, h * 0.3, w, h * 0.7);
    for (const T of towers) {
      const topY = h - T.th, cw = T.tw / T.cols;
      ctx.fillStyle = '#05070b'; ctx.fillRect(T.x, topY, T.tw, T.th);
      for (const win of T.wins) {
        const on = (Math.sin(t * 0.001 * (0.4 + win.flick) + win.lit * 6.28) + 1) / 2;
        if (on < 0.35) continue;
        ctx.fillStyle = win.flick > 0.85 ? cyan : bone; ctx.globalAlpha = 0.25 + on * 0.6;
        ctx.fillRect(T.x + win.c * cw + 2, topY + win.r * 12 + 2, cw - 4, 7);
      }
      ctx.globalAlpha = 1;
      const pulse = Math.abs(Math.sin(t * 0.0015 + T.beacon));
      ctx.fillStyle = red; ctx.globalAlpha = 0.3 + pulse * 0.7;
      ctx.beginPath(); ctx.arc(T.x + T.tw / 2, topY - 2, 2 + pulse * 2.5, 0, 6.2832); ctx.fill();
      ctx.globalAlpha = 1;
    }
  };
};
