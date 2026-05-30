// seam — "Inventory of a Borrowed Face"
//
// A symmetry that almost holds: a field of strokes mirrored across the center,
// the mirror nudged a few pixels off true. Down that fault line a slow light
// passes — the seam the mirror agrees to ignore, that the light keeps finding.
//
// Contract: return an optional step(t) for animation, or nothing for one frame.
window.__deckardSketch = function (ctx, w, h, rng, palette) {
  const [night, , grey, bone, accent] = palette;
  const cx = w / 2;
  const seam = 2 + rng() * 6; // the hairline at the jaw
  const cell = 14;
  const phase = [rng() * 6.28, rng() * 6.28, rng() * 6.28];

  function angle(x, y) {
    return (
      Math.sin(x * 0.010 + phase[0]) +
      Math.cos(y * 0.013 + phase[1]) +
      Math.sin((x + y) * 0.007 + phase[2])
    ) * 1.3;
  }

  function stroke(x, y, a, color, alpha) {
    const len = 9;
    ctx.strokeStyle = color;
    ctx.globalAlpha = alpha;
    ctx.lineWidth = 1.1;
    ctx.beginPath();
    ctx.moveTo(x - Math.cos(a) * len, y - Math.sin(a) * len);
    ctx.lineTo(x + Math.cos(a) * len, y + Math.sin(a) * len);
    ctx.stroke();
    ctx.globalAlpha = 1;
  }

  return function step(t) {
    ctx.fillStyle = night;
    ctx.fillRect(0, 0, w, h);
    for (let y = cell; y < h; y += cell) {
      for (let x = cell; x < cx; x += cell) {
        const a = angle(x, y);
        stroke(x, y, a, grey, 0.5); // the meant
        stroke(w - x + seam, y, Math.PI - a, bone, 0.32); // the made, off by a seam
      }
    }
    // the light that finds the seam at certain hours
    const sweep = 0.5 + 0.5 * Math.sin(t * 0.0006);
    const lx = cx + seam / 2;
    const glow = ctx.createLinearGradient(lx - 40, 0, lx + 40, 0);
    glow.addColorStop(0, 'rgba(0,0,0,0)');
    glow.addColorStop(0.5, accent);
    glow.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.globalAlpha = 0.06 + 0.14 * sweep;
    ctx.fillStyle = glow;
    ctx.fillRect(lx - 40, 0, 80, h);
    ctx.globalAlpha = 1;
  };
};
