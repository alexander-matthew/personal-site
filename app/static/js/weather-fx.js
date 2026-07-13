/**
 * WeatherFX — condition-driven halftone backdrops for the weather page.
 *
 * Builds greyscale source functions parameterized by effect kind and
 * intensity (see WeatherEngine.getEffect), and mounts them on a fixed
 * full-viewport canvas through the Halftone engine so every condition
 * renders in the site's dithered ice-blue plates:
 *
 *   rain   — falling streaks; count, length, speed and slant scale with
 *            intensity, under a soft cloud haze
 *   storm  — heavy rain plus scheduled lightning: a sky-wide brightening
 *            and a jagged bolt, deterministic per strike
 *   snow   — swaying flakes, slow and sparse to thick and wind-blown
 *   clouds — drifting fBm billows; intensity is sky coverage
 *   fog    — low-contrast noise field, denser toward the ground
 *   clear  — a faint sun disc and sparse twinkling dust
 *
 * Everything is deterministic (Halftone.util.hashCell) — no Math.random —
 * so frames never shimmer. Attaches a single global: `WeatherFX`.
 */
(function (global) {
    'use strict';

    function util() { return global.Halftone.util; }

    function grey(l) {
        var v = Math.round(util().clamp(l, 0, 1) * 255);
        return 'rgb(' + v + ',' + v + ',' + v + ')';
    }

    // Per-particle scalar in [0,1): particle index x salt, stable across frames.
    function prand(k, salt) {
        return util().hashCell(k + 1, salt * 131 + 7);
    }

    // ---------------------------------------------------------------
    // Shared scenery
    // ---------------------------------------------------------------

    // Soft haze along the top edge — the cloud deck precip falls from.
    function drawCloudHaze(ctx, w, h, depth) {
        var deckH = h * (0.18 + depth * 0.1);
        var g = ctx.createLinearGradient(0, 0, 0, deckH);
        g.addColorStop(0, 'rgba(70,70,70,' + (0.5 + depth * 0.4) + ')');
        g.addColorStop(1, 'rgba(40,40,40,0)');
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, w, deckH);
    }

    // ---------------------------------------------------------------
    // Precipitation (canvas primitives — cheap at offscreen scale)
    // ---------------------------------------------------------------

    function rainSource(intensity, stormy) {
        var i = util().clamp(intensity, 0, 1);
        var slant = 0.08 + i * 0.3;

        return function (ctx, w, h, t) {
            ctx.clearRect(0, 0, w, h);
            drawCloudHaze(ctx, w, h, stormy ? 1 : i);

            var count = Math.round((w * h) / 400 * (0.3 + 2.2 * i));
            var span = w * (1 + slant);
            var k, speed, len, phase, y, x, shade;

            ctx.lineWidth = 1;
            for (k = 0; k < count; k++) {
                speed = h * (0.55 + i * 0.75) * (0.7 + prand(k, 1) * 0.6);
                len = 2 + i * 5 + prand(k, 2) * 2;
                phase = prand(k, 3) * (h + len * 2);
                y = ((phase + t * speed) % (h + len * 2)) - len;
                x = ((prand(k, 4) * span - y * slant) % span + span) % span - w * slant * 0.5;

                shade = 0.3 + i * 0.15 + prand(k, 5) * 0.25;
                ctx.strokeStyle = grey(shade);
                ctx.beginPath();
                ctx.moveTo(x + slant * len, y - len);
                ctx.lineTo(x, y);
                ctx.stroke();
            }
        };
    }

    function stormSource(intensity) {
        var i = util().clamp(intensity, 0, 1);
        var rain = rainSource(0.65 + i * 0.35, true);
        var period = 7 - i * 3; // seconds between possible strikes

        // Flash envelope for the current moment: 0 when quiet, ~1 at the
        // instant of a strike, with a fast decay and an echo pulse.
        function flashAt(t) {
            var p = Math.floor(t / period);
            if (util().hashCell(p + 3, 77) > 0.3 + i * 0.4) { return { env: 0, p: p }; }
            var offset = util().hashCell(p + 3, 78) * (period - 1.2);
            var ft = t - (p * period + offset);
            if (ft < 0 || ft > 1.2) { return { env: 0, p: p }; }
            var env = Math.exp(-ft * 9) + 0.5 * Math.exp(-Math.pow(ft - 0.14, 2) * 240);
            return { env: util().clamp(env, 0, 1), p: p };
        }

        function drawBolt(ctx, w, h, p, env) {
            var segs = 7;
            var x = (0.2 + util().hashCell(p + 3, 79) * 0.6) * w;
            var y = h * 0.08;
            var stepY = (h * 0.55) / segs;
            var s;

            ctx.strokeStyle = 'rgba(255,255,255,' + util().clamp(env * 1.4, 0, 1) + ')';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(x, y);
            for (s = 1; s <= segs; s++) {
                x += (util().hashCell(p * 31 + s, 81) - 0.5) * w * 0.07;
                y += stepY * (0.7 + util().hashCell(p * 31 + s, 82) * 0.6);
                ctx.lineTo(x, y);
            }
            ctx.stroke();
        }

        return function (ctx, w, h, t) {
            rain(ctx, w, h, t);

            var flash = flashAt(t);
            if (flash.env > 0.02) {
                // Sky-wide brightening — lifts cells into the light plates.
                ctx.fillStyle = 'rgba(255,255,255,' + flash.env * 0.32 + ')';
                ctx.fillRect(0, 0, w, h * 0.75);
                if (flash.env > 0.15) { drawBolt(ctx, w, h, flash.p, flash.env); }
            }
        };
    }

    function snowSource(intensity) {
        var i = util().clamp(intensity, 0, 1);

        return function (ctx, w, h, t) {
            ctx.clearRect(0, 0, w, h);
            drawCloudHaze(ctx, w, h, i * 0.6);

            var count = Math.round((w * h) / 500 * (0.4 + 1.6 * i));
            var windDrift = w * 0.02 * i;
            var k, speed, sway, phase, y, x, shade;

            for (k = 0; k < count; k++) {
                speed = h * 0.07 * (0.6 + i * 0.7) * (0.7 + prand(k, 1) * 0.6);
                phase = prand(k, 2) * h * 1.2;
                y = ((phase + t * speed) % (h * 1.1)) - h * 0.05;
                sway = Math.sin(t * (0.4 + prand(k, 3) * 0.5) + prand(k, 4) * 6.28) * (1.5 + i * 2);
                x = ((prand(k, 5) * w + sway + t * windDrift) % w + w) % w;

                shade = 0.7 + prand(k, 6) * 0.3;
                ctx.fillStyle = grey(shade);
                ctx.fillRect(x, y, 1, 1);
            }
        };
    }

    // ---------------------------------------------------------------
    // Atmosphere (per-cell ImageData — small offscreen keeps it cheap)
    // ---------------------------------------------------------------

    function cloudsSource(intensity) {
        var i = util().clamp(intensity, 0, 1);
        var cover = 0.3 + i * 0.5;

        return function (ctx, w, h, t) {
            var U = util();
            var img = ctx.createImageData(w, h);
            var data = img.data;
            var prevRow = new Float32Array(w);
            var drift = t * 0.014;
            var x, y, ny, n, dens, shape, top, lum, idx;

            for (y = 0; y < h; y++) {
                ny = y / (h - 1 || 1);
                var env = 1 - U.smoothstep(0.5, 0.85, ny);
                for (x = 0; x < w; x++) {
                    n = U.fbm3((x / h) * 1.8 + drift, ny * 2.8 + drift * 0.2);
                    // Contrast-expand the noise so billow edges are crisp,
                    // then shift by coverage.
                    dens = (n - 0.5) * 1.8 + 0.5 + (cover - 0.52) * 0.9 - ny * 0.1;
                    shape = U.smoothstep(0.42, 0.74, dens) * env;

                    lum = 0;
                    if (shape > 0) {
                        top = y === 0 ? 0 : U.clamp((n - prevRow[x]) * 16, -0.25, 0.55);
                        lum = U.clamp(shape * (0.55 + top) * (1 - ny * 0.25), 0, 0.85);
                    }
                    prevRow[x] = n;

                    idx = (y * w + x) * 4;
                    data[idx] = data[idx + 1] = data[idx + 2] = (lum * 255) | 0;
                    data[idx + 3] = 255;
                }
            }
            ctx.putImageData(img, 0, 0);
        };
    }

    function fogSource(intensity) {
        var i = util().clamp(intensity, 0, 1);

        return function (ctx, w, h, t) {
            var U = util();
            var img = ctx.createImageData(w, h);
            var data = img.data;
            var drift = t * 0.008;
            var x, y, ny, n, lum, idx;

            for (y = 0; y < h; y++) {
                ny = y / (h - 1 || 1);
                for (x = 0; x < w; x++) {
                    n = U.fbm3((x / h) * 1.4 + drift, ny * 1.8 - drift * 0.4);
                    // Low-contrast bank, thicker toward the ground.
                    lum = (0.12 + n * 0.45 * i) * (0.4 + ny * 0.85);
                    idx = (y * w + x) * 4;
                    data[idx] = data[idx + 1] = data[idx + 2] = (U.clamp(lum, 0, 1) * 255) | 0;
                    data[idx + 3] = 255;
                }
            }
            ctx.putImageData(img, 0, 0);
        };
    }

    function clearSource(intensity) {
        var i = util().clamp(intensity, 0, 1);

        return function (ctx, w, h, t) {
            ctx.clearRect(0, 0, w, h);

            // Faint sun high right, breathing very slowly.
            var r = Math.min(w, h) * (0.3 + i * 0.15) * (1 + Math.sin(t * 0.15) * 0.04);
            var cx = w * 0.82, cy = h * 0.16;
            var g = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
            g.addColorStop(0, grey(0.5 + i * 0.2));
            g.addColorStop(0.35, grey(0.28));
            g.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = g;
            ctx.fillRect(cx - r, cy - r, r * 2, r * 2);

            // Sparse dust, each mote twinkling on its own clock.
            var count = Math.round((w * h) / 900);
            var k, x, y, tw;
            for (k = 0; k < count; k++) {
                x = prand(k, 11) * w;
                y = prand(k, 12) * h;
                tw = 0.12 + 0.14 * (Math.sin(t * 0.5 + prand(k, 13) * 6.28) + 1) / 2;
                ctx.fillStyle = grey(tw);
                ctx.fillRect(x, y, 1, 1);
            }
        };
    }

    var SOURCES = {
        rain: function (i) { return rainSource(i, false); },
        storm: stormSource,
        snow: snowSource,
        clouds: cloudsSource,
        fog: fogSource,
        clear: clearSource
    };

    // Precip needs frame rate; atmosphere can idle.
    var FPS = { rain: 30, storm: 30, snow: 30, clouds: 20, fog: 20, clear: 20 };

    // ---------------------------------------------------------------
    // Manager — one fixed canvas, crossfaded on condition change
    // ---------------------------------------------------------------

    var WeatherFX = {
        _canvas: null,
        _instance: null,
        _current: null,
        _swapTimer: null,

        mount: function (canvas) {
            this._canvas = canvas;
        },

        set: function (effect, intensity) {
            if (!this._canvas || !global.Halftone || !SOURCES[effect]) { return; }
            var key = effect + ':' + intensity;
            if (this._current === key) { return; }
            this._current = key;

            var self = this;
            var swap = function () {
                if (self._instance) { self._instance.destroy(); }
                self._instance = global.Halftone.mount(self._canvas, {
                    source: SOURCES[effect](intensity),
                    cell: 6,
                    style: 'dot',
                    fps: FPS[effect] || 24
                });
                self._canvas.classList.add('on');
            };

            if (this._swapTimer) { global.clearTimeout(this._swapTimer); }
            if (this._instance) {
                // Fade out the old condition, then mount the new one.
                this._canvas.classList.remove('on');
                this._swapTimer = global.setTimeout(swap, 650);
            } else {
                swap();
            }
        }
    };

    global.WeatherFX = WeatherFX;
})(window);
