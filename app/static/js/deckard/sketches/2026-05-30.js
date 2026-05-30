// nightwatch — "Field Notes Before Sleep"
//
// A skyline that blinks back. Towers raised at random across the glass, windows
// guttering on and off, red beacons pulsing their slow awake, awake, awake.
// Every refresh is a city that never was, and never will be again.
//
// Contract: return an optional step(t) for animation, or nothing for one frame.
window.__deckardSketch = function (ctx, w, h, rng, palette) {
  const [night, deep, red, cyan, bone] = palette;
  const towers = [];

  let x = -20;
  while (x < w + 20) {
    const tw = 22 + rng() * 60;
    const th = h * (0.25 + rng() * 0.55);
    const cols = Math.max(1, Math.floor(tw / 10));
    const rows = Math.floor(th / 12);
    const windows = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (rng() < 0.55) windows.push({ c, r, lit: rng(), flick: rng() });
      }
    }
    towers.push({ x, tw, th, cols, windows, beacon: rng() * 6.28 });
    x += tw + 4 + rng() * 10;
  }

  return function step(t) {
    ctx.fillStyle = night;
    ctx.fillRect(0, 0, w, h);
    const haze = ctx.createLinearGradient(0, h, 0, h * 0.3);
    haze.addColorStop(0, deep);
    haze.addColorStop(1, night);
    ctx.fillStyle = haze;
    ctx.fillRect(0, h * 0.3, w, h * 0.7);

    for (const tower of towers) {
      const topY = h - tower.th;
      ctx.fillStyle = '#05070b';
      ctx.fillRect(tower.x, topY, tower.tw, tower.th);

      const cw = tower.tw / tower.cols;
      for (const win of tower.windows) {
        const on = (Math.sin(t * 0.001 * (0.4 + win.flick) + win.lit * 6.28) + 1) / 2;
        if (on < 0.35) continue;
        ctx.fillStyle = win.flick > 0.85 ? cyan : bone;
        ctx.globalAlpha = 0.25 + on * 0.6;
        ctx.fillRect(tower.x + win.c * cw + 2, topY + win.r * 12 + 2, cw - 4, 7);
      }
      ctx.globalAlpha = 1;

      const pulse = Math.abs(Math.sin(t * 0.0015 + tower.beacon));
      ctx.fillStyle = red;
      ctx.globalAlpha = 0.3 + pulse * 0.7;
      ctx.beginPath();
      ctx.arc(tower.x + tower.tw / 2, topY - 2, 2 + pulse * 2.5, 0, 6.2832);
      ctx.fill();
      ctx.globalAlpha = 1;
    }

    ctx.globalAlpha = 0.04;
    ctx.fillStyle = cyan;
    for (let y = 0; y < h; y += 3) ctx.fillRect(0, y, w, 1);
    ctx.globalAlpha = 1;
  };
};
