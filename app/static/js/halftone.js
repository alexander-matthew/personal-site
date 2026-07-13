/**
 * Halftone — zero-dependency vanilla-JS halftone/dither renderer.
 *
 * Signature visual element of the "Gravure" design language (see
 * docs/ai/design-language.md, §4). Renders a greyscale procedural or image
 * source through a stamped dot-grid or ordered (Bayer) dither, coloring
 * cells from a 4-step luminance-bucketed plate.
 *
 * No modules, no build step. Attaches a single global: `Halftone`.
 *
 * Usage:
 *   Halftone.mount(canvasEl, {
 *     source: Halftone.sources.clouds, // (ctx, w, h, t) => void, or an <img>
 *     cell: 7,
 *     style: 'dot',                   // 'dot' | 'bayer'
 *     plates: { shadow, mid, light, paper },
 *     fps: 30,
 *     animate: true,
 *   });
 *
 * Canvases with a `data-halftone="clouds|waves|columns"` attribute are mounted
 * automatically on DOMContentLoaded (see Halftone.sources / autoInit below).
 */
(function (global) {
    'use strict';

    // ---------------------------------------------------------------
    // Small deterministic helpers
    // ---------------------------------------------------------------

    // Deterministic hash of two integers -> float in [0, 1).
    // Never Math.random() — must be stable per-cell across frames so the
    // dot grid doesn't shimmer/moire during animation.
    function hashCell(x, y) {
        var h = (x * 374761393 + y * 668265263) | 0;
        h = (h ^ (h >>> 13)) | 0;
        h = Math.imul(h, 1274126177);
        h = (h ^ (h >>> 16)) >>> 0;
        return (h % 100000) / 100000;
    }

    // Classic 4x4 Bayer ordered-dither matrix (values 0..15).
    var BAYER4 = [
        [0, 8, 2, 10],
        [12, 4, 14, 6],
        [3, 11, 1, 9],
        [15, 7, 13, 5]
    ];

    function clamp(v, lo, hi) {
        return v < lo ? lo : (v > hi ? hi : v);
    }

    function mergePlates(plates) {
        var defaults = { shadow: '#0d1b2e', mid: '#4da6ff', light: '#a9d2ff', paper: '#f2f6fb' };
        var out = {};
        var k;
        for (k in defaults) { out[k] = defaults[k]; }
        if (plates) {
            for (k in plates) {
                if (plates[k]) { out[k] = plates[k]; }
            }
        }
        return out;
    }

    // Luminance (0..1) -> plate color, or null for "nothing" (background
    // shows through). Buckets: <0.18 none, then shadow/mid/light/paper.
    function plateForLuminance(lum, plates) {
        if (lum < 0.18) { return null; }
        if (lum < 0.45) { return plates.shadow; }
        if (lum < 0.68) { return plates.mid; }
        if (lum < 0.88) { return plates.light; }
        return plates.paper;
    }

    function prefersReducedMotion() {
        return !!(global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches);
    }

    // ---------------------------------------------------------------
    // Cell stamping
    // ---------------------------------------------------------------

    function stampCells(ctx, data, cols, rows, cell, style, plates) {
        var cx, cy, idx, a, lum, color, jitterA, jitterB, radius, px, py, thresh;

        for (cy = 0; cy < rows; cy++) {
            for (cx = 0; cx < cols; cx++) {
                idx = (cy * cols + cx) * 4;
                a = data[idx + 3];
                if (a === 0) { continue; }

                lum = (0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2]) / 255;
                lum *= a / 255;

                color = plateForLuminance(lum, plates);
                if (!color) { continue; }

                if (style === 'bayer') {
                    thresh = (BAYER4[cy & 3][cx & 3] + 0.5) / 16;
                    if (lum <= thresh) { continue; }
                    ctx.fillStyle = color;
                    ctx.fillRect(cx * cell, cy * cell, cell + 0.5, cell + 0.5);
                } else {
                    jitterA = hashCell(cx, cy) - 0.5;
                    jitterB = hashCell(cy, cx) - 0.5;
                    radius = clamp(lum * 0.62 * cell + jitterA * cell * 0.1, 0.4, cell * 0.62);
                    px = cx * cell + cell / 2 + jitterA * cell * 0.08;
                    py = cy * cell + cell / 2 + jitterB * cell * 0.08;

                    ctx.beginPath();
                    ctx.arc(px, py, radius, 0, Math.PI * 2);
                    ctx.fillStyle = color;
                    ctx.fill();
                }
            }
        }
    }

    // ---------------------------------------------------------------
    // Instance
    // ---------------------------------------------------------------

    function Instance(canvas, opts) {
        opts = opts || {};
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.cell = opts.cell || 6;
        this.style = opts.style === 'bayer' ? 'bayer' : 'dot';
        this.plates = mergePlates(opts.plates);
        this.fps = opts.fps || 30;
        this.frameInterval = 1000 / this.fps;
        this.wantsAnimate = opts.animate !== false;
        this.reducedMotion = prefersReducedMotion();
        this.animating = this.wantsAnimate && !this.reducedMotion;

        this.sourceFn = resolveSource(opts.source);

        this.offCanvas = document.createElement('canvas');
        this.offCtx = this.offCanvas.getContext('2d', { willReadFrequently: true });

        this.cols = 1;
        this.rows = 1;
        this.dpr = global.devicePixelRatio || 1;
        this.visible = true;
        this.currentT = 0;
        this.startTime = null;
        this.lastFrame = 0;
        this.rafId = null;
        this._resizeTimer = null;

        var self = this;

        // Initial size + first paint.
        this._resize();

        // Resize handling (debounced). Prefer ResizeObserver on the
        // element; fall back to window resize.
        if (typeof ResizeObserver !== 'undefined') {
            this._ro = new ResizeObserver(function () { self._scheduleResize(); });
            this._ro.observe(canvas);
        } else {
            this._onWindowResize = function () { self._scheduleResize(); };
            global.addEventListener('resize', this._onWindowResize);
        }

        // Pause when scrolled offscreen.
        if ('IntersectionObserver' in global) {
            this._io = new IntersectionObserver(function (entries) {
                self.visible = entries[0].isIntersecting;
            }, { threshold: 0 });
            this._io.observe(canvas);
        }

        // React live to prefers-reduced-motion changes.
        if (global.matchMedia) {
            this._mql = global.matchMedia('(prefers-reduced-motion: reduce)');
            this._onMqlChange = function (e) {
                self.reducedMotion = e.matches;
                self.animating = self.wantsAnimate && !self.reducedMotion;
                if (self.animating && self.rafId === null) {
                    self.lastFrame = 0;
                    self._loop();
                } else if (!self.animating) {
                    self._render(0);
                }
            };
            if (this._mql.addEventListener) {
                this._mql.addEventListener('change', this._onMqlChange);
            } else if (this._mql.addListener) {
                this._mql.addListener(this._onMqlChange);
            }
        }

        if (this.animating) {
            this._loop();
        }
    }

    function resolveSource(source) {
        if (typeof source === 'function') {
            return source;
        }
        if (source && source.tagName === 'IMG') {
            return function (ctx, w, h) {
                ctx.clearRect(0, 0, w, h);
                try { ctx.drawImage(source, 0, 0, w, h); } catch (e) { /* not loaded / tainted */ }
            };
        }
        return function () {};
    }

    Instance.prototype._scheduleResize = function () {
        var self = this;
        if (this._resizeTimer) { global.clearTimeout(this._resizeTimer); }
        this._resizeTimer = global.setTimeout(function () {
            self._resize();
        }, 120);
    };

    Instance.prototype._resize = function () {
        var rect = this.canvas.getBoundingClientRect();
        var cssW = Math.max(1, Math.round(rect.width) || this.canvas.clientWidth || 1);
        var cssH = Math.max(1, Math.round(rect.height) || this.canvas.clientHeight || 1);

        this.dpr = global.devicePixelRatio || 1;
        this.cssW = cssW;
        this.cssH = cssH;
        this.cols = Math.max(1, Math.round(cssW / this.cell));
        this.rows = Math.max(1, Math.round(cssH / this.cell));

        this.offCanvas.width = this.cols;
        this.offCanvas.height = this.rows;

        this.canvas.width = Math.round(cssW * this.dpr);
        this.canvas.height = Math.round(cssH * this.dpr);

        this._render(this.currentT || 0);
    };

    Instance.prototype._render = function (t) {
        this.currentT = t;

        var octx = this.offCtx, ow = this.cols, oh = this.rows;
        octx.clearRect(0, 0, ow, oh);
        try {
            this.sourceFn(octx, ow, oh, t);
        } catch (e) {
            return;
        }

        var data;
        try {
            data = octx.getImageData(0, 0, ow, oh).data;
        } catch (e) {
            return; // e.g. tainted canvas from a cross-origin image source
        }

        var ctx = this.ctx;
        ctx.save();
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        ctx.restore();
        ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);

        stampCells(ctx, data, ow, oh, this.cell, this.style, this.plates);
    };

    Instance.prototype._loop = function () {
        var self = this;
        this.rafId = global.requestAnimationFrame(function (ts) {
            self.rafId = null;
            if (self.startTime === null) { self.startTime = ts; }
            if (self.animating) { self._loop(); }
            if (!self.visible || !self.animating) { return; }
            if (ts - self.lastFrame < self.frameInterval) { return; }
            self.lastFrame = ts;
            self._render((ts - self.startTime) / 1000);
        });
    };

    Instance.prototype.destroy = function () {
        if (this.rafId !== null) { global.cancelAnimationFrame(this.rafId); }
        if (this._resizeTimer) { global.clearTimeout(this._resizeTimer); }
        if (this._ro) { this._ro.disconnect(); }
        if (this._io) { this._io.disconnect(); }
        if (this._onWindowResize) { global.removeEventListener('resize', this._onWindowResize); }
        if (this._mql) {
            if (this._mql.removeEventListener) { this._mql.removeEventListener('change', this._onMqlChange); }
            else if (this._mql.removeListener) { this._mql.removeListener(this._onMqlChange); }
        }
    };

    // ---------------------------------------------------------------
    // Procedural greyscale sources
    // ---------------------------------------------------------------

    function toGrey(l) {
        var v = Math.round(clamp(l, 0, 1) * 255);
        return 'rgb(' + v + ',' + v + ',' + v + ')';
    }

    function smoothstep(e0, e1, x) {
        var s = clamp((x - e0) / (e1 - e0), 0, 1);
        return s * s * (3 - 2 * s);
    }

    // Value noise on the hashCell lattice, bilinear with smooth fade.
    function vnoise(x, y) {
        var xi = Math.floor(x), yi = Math.floor(y);
        var xf = x - xi, yf = y - yi;
        var u = xf * xf * (3 - 2 * xf);
        var v = yf * yf * (3 - 2 * yf);
        var a = hashCell(xi, yi);
        var b = hashCell(xi + 1, yi);
        var c = hashCell(xi, yi + 1);
        var d = hashCell(xi + 1, yi + 1);
        return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
    }

    // Three-octave fBm, normalized to ~[0,1]. Octave offsets decorrelate
    // the lattices so billow edges don't align.
    function fbm3(x, y) {
        var s = 0.5 * vnoise(x, y);
        s += 0.25 * vnoise(x * 2.02 + 19.3, y * 2.02 + 7.1);
        s += 0.125 * vnoise(x * 4.05 + 53.1, y * 4.05 + 31.7);
        return s / 0.875;
    }

    // Drifting cloudbank over a dark sky — the full-bleed hero backdrop.
    // fBm billows shaped by a vertical envelope: sparse dust above, a
    // luminous bank of cloud tops mid-frame (lit from above via the
    // row-to-row density derivative), fading to clean ink in the lower
    // third so display type sits on black. Writes greyscale ImageData
    // directly — at offscreen scale (cols x rows) this is cheap.
    function clouds(ctx, w, h, t) {
        t = t || 0;

        var img = ctx.createImageData(w, h);
        var data = img.data;
        var prevRow = new Float32Array(w);
        var drift = t * 0.016;

        var x, y, ny, u, n, far, dens, shape, top, lum, sky, fade, idx;
        for (y = 0; y < h; y++) {
            ny = y / (h - 1 || 1);
            // Where the main bank lives: none at the very top, densest
            // ~55%, gone by ~85% of the height.
            var env = smoothstep(0.04, 0.42, ny) * (1 - smoothstep(0.55, 0.85, ny));
            // A second, distant layer high in the sky for depth.
            var envFar = smoothstep(0.02, 0.16, ny) * (1 - smoothstep(0.3, 0.5, ny));
            fade = 1 - smoothstep(0.68, 0.94, ny);

            for (x = 0; x < w; x++) {
                u = x / h;
                n = fbm3(u * 1.7 + drift, ny * 2.6 + drift * 0.22);

                dens = n + (env - 0.55) * 0.6;
                shape = smoothstep(0.38, 0.72, dens);

                lum = 0;
                if (shape > 0) {
                    // Density increasing downward = a cloud's upper edge —
                    // brighten it (sun-from-above rim light).
                    top = y === 0 ? 0 : clamp((n - prevRow[x]) * 20, -0.3, 0.75);
                    lum = shape * (0.68 + top) * (1.2 - ny * 0.7);
                }

                // Distant bank: smaller features drifting slower, dim
                // enough to stay on the shadow/mid plates.
                if (envFar > 0 && shape < 1) {
                    far = vnoise(u * 4.2 + drift * 0.5 + 40.7, ny * 6.5 + 60.2);
                    far = smoothstep(0.55, 0.8, far + (envFar - 0.7) * 0.5) * 0.38;
                    if (far > lum) { lum = far; }
                }

                // Sparse dust in the open sky, densest near the bank.
                sky = (0.12 + n * 0.1) * (1 - shape) * env;
                if (sky > lum) { lum = sky; }
                lum = clamp(lum * fade, 0, 1);

                prevRow[x] = n;

                idx = (y * w + x) * 4;
                data[idx] = data[idx + 1] = data[idx + 2] = (lum * 255) | 0;
                data[idx + 3] = 255;
            }
        }

        ctx.putImageData(img, 0, 0);
    }

    // 4-6 layered horizontal sine bands, each a soft vertical gradient,
    // slowly drifting phase.
    function waves(ctx, w, h, t) {
        t = t || 0;
        ctx.clearRect(0, 0, w, h);

        var bands = 5;
        var bandH = h / bands;
        var step = Math.max(2, w / 32);
        var i, phase, y0, amp, base, grad, x, yy;

        for (i = 0; i < bands; i++) {
            phase = t * 0.3 + i * 1.3;
            y0 = i * bandH;
            amp = bandH * 0.18;
            base = 0.25 + 0.5 * ((Math.sin(phase * 0.6 + i) + 1) / 2);

            grad = ctx.createLinearGradient(0, y0, 0, y0 + bandH);
            grad.addColorStop(0, toGrey(base + 0.35));
            grad.addColorStop(1, toGrey(base - 0.35));

            ctx.beginPath();
            ctx.moveTo(0, y0 + Math.sin(phase) * amp);
            for (x = 0; x <= w; x += step) {
                yy = y0 + Math.sin(phase + x * 0.02) * amp;
                ctx.lineTo(x, yy);
            }
            for (x = w; x >= 0; x -= step) {
                yy = y0 + bandH + Math.sin(phase + 1 + x * 0.02) * amp;
                ctx.lineTo(x, yy);
            }
            ctx.closePath();
            ctx.fillStyle = grad;
            ctx.fill();
        }
    }

    // Vertical bands alternating light/dark like fluted glass, with a
    // gentle luminance "breathing" over time.
    function columns(ctx, w, h, t) {
        t = t || 0;
        ctx.clearRect(0, 0, w, h);

        var count = 10;
        var colW = w / count;
        var i, breathing, base, lum, grad, edgeLum, midLum;

        for (i = 0; i < count; i++) {
            breathing = (Math.sin(t * 0.2 + i * 0.6) + 1) / 2;
            base = (i % 2 === 0) ? 0.72 : 0.28;
            lum = base * 0.7 + breathing * 0.3;
            edgeLum = clamp(lum - 0.25, 0, 1);
            midLum = clamp(lum + 0.15, 0, 1);

            grad = ctx.createLinearGradient(i * colW, 0, (i + 1) * colW, 0);
            grad.addColorStop(0, toGrey(edgeLum));
            grad.addColorStop(0.5, toGrey(midLum));
            grad.addColorStop(1, toGrey(edgeLum));

            ctx.fillStyle = grad;
            ctx.fillRect(i * colW, 0, colW + 1, h);
        }
    }

    // ---------------------------------------------------------------
    // Auto-init from data attributes
    // ---------------------------------------------------------------

    function parseBool(val, fallback) {
        if (val === null || val === undefined) { return fallback; }
        return val !== 'false' && val !== '0';
    }

    function autoInit() {
        var canvases = document.querySelectorAll('canvas[data-halftone]');
        var i, canvas, name, source, cell, style, animate, fps;

        for (i = 0; i < canvases.length; i++) {
            canvas = canvases[i];
            name = canvas.getAttribute('data-halftone');
            source = Halftone.sources[name];
            if (!source) { continue; }

            cell = parseFloat(canvas.getAttribute('data-cell'));
            if (!cell || cell <= 0) { cell = 6; }
            style = canvas.getAttribute('data-style') === 'bayer' ? 'bayer' : 'dot';
            animate = parseBool(canvas.getAttribute('data-animate'), true);
            fps = parseFloat(canvas.getAttribute('data-fps'));
            if (!fps || fps <= 0) { fps = 30; }

            Halftone.mount(canvas, { source: source, cell: cell, style: style, animate: animate, fps: fps });
        }
    }

    // ---------------------------------------------------------------
    // Public API
    // ---------------------------------------------------------------

    var Halftone = {
        mount: function (canvas, opts) {
            return new Instance(canvas, opts);
        },
        sources: {
            clouds: clouds,
            waves: waves,
            columns: columns
        },
        // Deterministic drawing helpers for page-specific sources
        // (e.g. weather-fx.js) — same rules apply: never Math.random().
        util: {
            hashCell: hashCell,
            clamp: clamp,
            smoothstep: smoothstep,
            vnoise: vnoise,
            fbm3: fbm3
        },
        autoInit: autoInit
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoInit);
    } else {
        autoInit();
    }

    global.Halftone = Halftone;
})(window);
