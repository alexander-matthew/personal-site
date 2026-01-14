/**
 * Generative Art Gallery
 * Live p5.js editor with thumbnail carousel navigation
 *
 * SECURITY NOTE: This file intentionally uses dynamic code execution (new Function)
 * to enable live code editing. This is the same pattern used by CodePen, Shadertoy,
 * and similar creative coding tools. The code executes only in the user's browser
 * on their own session - there is no server-side execution or persistent storage.
 */

// Import CodeMirror modules via esm.sh (handles ES module bundling properly)
import { EditorView, basicSetup } from 'https://esm.sh/codemirror@6.0.1';
import { javascript } from 'https://esm.sh/@codemirror/lang-javascript@6.2.1';
import { oneDark } from 'https://esm.sh/@codemirror/theme-one-dark@6.1.2';
import { autocompletion } from 'https://esm.sh/@codemirror/autocomplete@6.11.1';
import { linter, lintGutter } from 'https://esm.sh/@codemirror/lint@6.4.2';

// ============================================================================
// Sketch Registry
// ============================================================================

const SKETCHES = [
    {
        id: 'flowing-particles',
        name: 'Flowing Particles',
        tags: ['particles', 'noise', 'motion'],
        code: `// Flowing Particles
// Particles follow a noise-based flow field

let particles = [];
const numParticles = 500;
const noiseScale = 0.01;

function setup() {
    createCanvas(600, 600);
    background(10);

    // Initialize particles
    for (let i = 0; i < numParticles; i++) {
        particles.push({
            x: random(width),
            y: random(height),
            prevX: 0,
            prevY: 0
        });
    }
}

function draw() {
    // Fade effect
    fill(10, 10, 10, 15);
    noStroke();
    rect(0, 0, width, height);

    // Update and draw particles
    stroke(100, 180, 255, 50);
    strokeWeight(1);

    for (let p of particles) {
        p.prevX = p.x;
        p.prevY = p.y;

        // Flow field angle from noise
        let angle = noise(p.x * noiseScale, p.y * noiseScale, frameCount * 0.005) * TWO_PI * 2;

        // Move particle
        p.x += cos(angle) * 2;
        p.y += sin(angle) * 2;

        // Draw trail
        line(p.prevX, p.prevY, p.x, p.y);

        // Wrap around edges
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;
    }
}`
    },
    {
        id: 'geometric-spiral',
        name: 'Geometric Spiral',
        tags: ['geometry', 'spiral', 'colorful'],
        code: `// Geometric Spiral
// Rotating shapes form a hypnotic spiral

let angle = 0;
let hueOffset = 0;

function setup() {
    createCanvas(600, 600);
    colorMode(HSB, 360, 100, 100, 100);
    rectMode(CENTER);
}

function draw() {
    background(0, 0, 10);
    translate(width / 2, height / 2);

    for (let i = 0; i < 100; i++) {
        let size = map(i, 0, 100, 10, 300);
        let rotation = angle + i * 0.1;
        let hue = (hueOffset + i * 3) % 360;

        push();
        rotate(rotation);
        noFill();
        stroke(hue, 70, 90, 60);
        strokeWeight(2);

        // Alternate between shapes
        if (i % 3 === 0) {
            rect(0, 0, size, size);
        } else if (i % 3 === 1) {
            ellipse(0, 0, size, size);
        } else {
            triangle(
                0, -size / 2,
                -size / 2, size / 2,
                size / 2, size / 2
            );
        }
        pop();
    }

    angle += 0.01;
    hueOffset += 0.5;
}`
    },
    {
        id: 'wave-interference',
        name: 'Wave Interference',
        tags: ['waves', 'math', 'interference'],
        code: `// Wave Interference
// Multiple wave sources create interference patterns

const sources = [];
const numSources = 3;

function setup() {
    createCanvas(600, 600);
    pixelDensity(1);

    // Create wave sources
    for (let i = 0; i < numSources; i++) {
        sources.push({
            x: random(width),
            y: random(height),
            frequency: random(0.02, 0.05),
            phase: random(TWO_PI)
        });
    }
}

function draw() {
    loadPixels();

    for (let x = 0; x < width; x++) {
        for (let y = 0; y < height; y++) {
            let sum = 0;

            // Sum waves from all sources
            for (let source of sources) {
                let d = dist(x, y, source.x, source.y);
                sum += sin(d * source.frequency - frameCount * 0.05 + source.phase);
            }

            // Map sum to color
            let brightness = map(sum, -numSources, numSources, 0, 255);
            let hue = map(sum, -numSources, numSources, 180, 280);

            // Convert HSB to RGB (simplified)
            let r = brightness * 0.3;
            let g = brightness * 0.5;
            let b = brightness;

            let idx = (x + y * width) * 4;
            pixels[idx] = r;
            pixels[idx + 1] = g;
            pixels[idx + 2] = b;
            pixels[idx + 3] = 255;
        }
    }

    updatePixels();

    // Slowly move sources
    for (let source of sources) {
        source.x += sin(frameCount * 0.01 + source.phase) * 0.5;
        source.y += cos(frameCount * 0.01 + source.phase) * 0.5;

        // Bounce off edges
        if (source.x < 0 || source.x > width) source.x = constrain(source.x, 0, width);
        if (source.y < 0 || source.y > height) source.y = constrain(source.y, 0, height);
    }
}`
    },
    {
        id: 'recursive-tree',
        name: 'Recursive Tree',
        tags: ['recursive', 'nature', 'fractal'],
        code: `// Recursive Tree
// Wind-swaying fractal tree

let windOffset = 0;

function setup() {
    createCanvas(600, 600);
}

function draw() {
    background(20, 25, 35);

    // Ground
    fill(30, 35, 45);
    noStroke();
    rect(0, height - 50, width, 50);

    // Draw tree from bottom center
    translate(width / 2, height - 50);

    stroke(80, 60, 50);
    strokeWeight(12);

    // Start recursion
    branch(120, 0);

    windOffset += 0.02;
}

function branch(len, depth) {
    if (len < 4 || depth > 12) return;

    // Wind effect increases with height
    let wind = sin(windOffset + depth * 0.3) * map(depth, 0, 12, 0, 0.1);

    // Draw branch
    let sw = map(len, 4, 120, 1, 12);
    strokeWeight(sw);

    // Color shifts from brown to green
    let g = map(depth, 0, 12, 60, 150);
    stroke(80, g, 50);

    line(0, 0, 0, -len);
    translate(0, -len);

    // Branch off
    let newLen = len * 0.72;
    let angle = PI / 6 + wind;

    push();
    rotate(angle);
    branch(newLen, depth + 1);
    pop();

    push();
    rotate(-angle * 0.9);
    branch(newLen, depth + 1);
    pop();

    // Sometimes add a third branch
    if (random() > 0.6 && depth < 8) {
        push();
        rotate(wind * 2);
        branch(newLen * 0.8, depth + 1);
        pop();
    }
}`
    },
    {
        id: 'circle-packing',
        name: 'Circle Packing',
        tags: ['circles', 'packing', 'generative'],
        code: `// Circle Packing
// Circles grow until they touch

let circles = [];
const maxAttempts = 500;
const growthRate = 0.5;

function setup() {
    createCanvas(600, 600);
    background(15);
    noLoop(); // We'll manually call draw

    // Generate circles
    generateCircles();

    // Draw them
    drawCircles();
}

function generateCircles() {
    for (let i = 0; i < maxAttempts; i++) {
        let newCircle = {
            x: random(width),
            y: random(height),
            r: 2,
            growing: true,
            hue: random(360)
        };

        // Check if position is valid
        let valid = true;
        for (let c of circles) {
            let d = dist(newCircle.x, newCircle.y, c.x, c.y);
            if (d < c.r + newCircle.r + 2) {
                valid = false;
                break;
            }
        }

        if (valid) {
            circles.push(newCircle);
        }
    }

    // Grow circles
    let growing = true;
    while (growing) {
        growing = false;
        for (let c of circles) {
            if (c.growing) {
                c.r += growthRate;
                growing = true;

                // Check edges
                if (c.x - c.r < 0 || c.x + c.r > width ||
                    c.y - c.r < 0 || c.y + c.r > height) {
                    c.growing = false;
                }

                // Check other circles
                for (let other of circles) {
                    if (c !== other) {
                        let d = dist(c.x, c.y, other.x, other.y);
                        if (d < c.r + other.r + 2) {
                            c.growing = false;
                            break;
                        }
                    }
                }
            }
        }
    }
}

function drawCircles() {
    colorMode(HSB, 360, 100, 100, 100);

    for (let c of circles) {
        noFill();
        stroke(c.hue, 60, 80, 80);
        strokeWeight(2);
        ellipse(c.x, c.y, c.r * 2);

        // Inner detail
        if (c.r > 15) {
            stroke(c.hue, 40, 90, 40);
            strokeWeight(1);
            ellipse(c.x, c.y, c.r * 1.5);
        }
    }
}

function mousePressed() {
    // Regenerate on click
    circles = [];
    background(15);
    generateCircles();
    drawCircles();
}`
    },
    {
        id: 'starfield',
        name: 'Starfield',
        tags: ['space', '3d', 'animation'],
        code: `// Starfield
// Classic 3D starfield effect

let stars = [];
const numStars = 400;
const speed = 5;

function setup() {
    createCanvas(600, 600);

    // Initialize stars
    for (let i = 0; i < numStars; i++) {
        stars.push({
            x: random(-width / 2, width / 2),
            y: random(-height / 2, height / 2),
            z: random(width),
            pz: 0 // previous z for trails
        });
    }
}

function draw() {
    background(0);
    translate(width / 2, height / 2);

    for (let star of stars) {
        star.pz = star.z;
        star.z -= speed;

        // Reset star if it passes the camera
        if (star.z < 1) {
            star.x = random(-width / 2, width / 2);
            star.y = random(-height / 2, height / 2);
            star.z = width;
            star.pz = star.z;
        }

        // Project to 2D
        let sx = map(star.x / star.z, 0, 1, 0, width / 2);
        let sy = map(star.y / star.z, 0, 1, 0, height / 2);

        // Previous position for trail
        let px = map(star.x / star.pz, 0, 1, 0, width / 2);
        let py = map(star.y / star.pz, 0, 1, 0, height / 2);

        // Size based on depth
        let r = map(star.z, 0, width, 4, 0);

        // Color - closer stars are brighter and bluer
        let brightness = map(star.z, 0, width, 255, 50);
        let blue = map(star.z, 0, width, 255, 150);

        stroke(brightness, brightness, blue);
        strokeWeight(r);
        line(px, py, sx, sy);
    }
}`
    },
    {
        id: 'agnes-martin-grid',
        name: 'Trembling Grid (Agnes Martin)',
        tags: ['minimalist', 'grid', 'meditative'],
        code: `// Trembling Grid - Inspired by Agnes Martin
// Delicate hand-drawn lines forming subtle grids
// Martin's work evokes stillness and contemplation

const gridSize = 20;
const canvasSize = 600;
let lineOffset = [];

function setup() {
    createCanvas(canvasSize, canvasSize);
    generateOffsets();
    noLoop();
}

function generateOffsets() {
    lineOffset = [];
    let numLines = Math.ceil(canvasSize / gridSize) + 1;
    let numPoints = Math.ceil(canvasSize / 5) + 1;

    for (let i = 0; i < numLines; i++) {
        lineOffset.push([]);
        for (let j = 0; j < numPoints; j++) {
            lineOffset[i].push(random(-0.5, 0.5));
        }
    }
}

function draw() {
    // Soft, warm off-white background
    background(252, 250, 245);

    // Pale blue-gray for lines (Martin's signature palette)
    stroke(180, 190, 200, 80);
    strokeWeight(0.5);

    // Draw horizontal lines with subtle hand-drawn wobble
    for (let y = gridSize; y < canvasSize - gridSize; y += gridSize) {
        let lineIdx = floor(y / gridSize);
        if (!lineOffset[lineIdx]) continue;

        beginShape();
        noFill();
        for (let x = gridSize; x <= canvasSize - gridSize; x += 5) {
            let idx = floor((x - gridSize) / 5);
            let wobble = (lineOffset[lineIdx] && lineOffset[lineIdx][idx]) ? lineOffset[lineIdx][idx] : 0;
            vertex(x, y + wobble + sin(x * 0.02) * 0.3);
        }
        endShape();
    }

    // Vertical lines - even more subtle
    stroke(180, 190, 200, 40);
    for (let x = gridSize; x < canvasSize - gridSize; x += gridSize) {
        beginShape();
        noFill();
        for (let y = gridSize; y <= canvasSize - gridSize; y += 5) {
            let wobble = random(-0.3, 0.3);
            vertex(x + wobble + sin(y * 0.02) * 0.2, y);
        }
        endShape();
    }

    // Soft vignette effect
    noStroke();
    for (let i = 0; i < 50; i++) {
        fill(252, 250, 245, 5);
        rect(0, 0, i * 2, canvasSize);
        rect(canvasSize - i * 2, 0, i * 2, canvasSize);
        rect(0, 0, canvasSize, i * 2);
        rect(0, canvasSize - i * 2, canvasSize, i * 2);
    }
}

function mousePressed() {
    generateOffsets();
    redraw();
}`
    },
    {
        id: 'de-kooning-gesture',
        name: 'Gestural Abstraction (de Kooning)',
        tags: ['expressionist', 'gestural', 'bold'],
        code: `// Gestural Abstraction - Inspired by Willem de Kooning
// Bold, energetic brushstrokes with vibrant colors
// Capturing the raw energy of abstract expressionism

let strokes = [];

function setup() {
    createCanvas(600, 600);
    background(245, 240, 235);
    generateStrokes();
    noLoop();
}

function generateStrokes() {
    strokes = [];

    // Generate bold gestural strokes
    for (let i = 0; i < 25; i++) {
        strokes.push({
            points: generateGesture(),
            color: getDeKooningColor(),
            weight: random(15, 60),
            alpha: random(150, 255)
        });
    }
}

function generateGesture() {
    let points = [];
    let x = random(width);
    let y = random(height);
    let angle = random(TWO_PI);
    let length = random(100, 400);
    let segments = floor(length / 10);

    for (let i = 0; i < segments; i++) {
        points.push({ x, y });

        // Energetic, sweeping movement
        angle += random(-0.5, 0.5);
        let speed = random(10, 25);
        x += cos(angle) * speed;
        y += sin(angle) * speed;

        // Occasional sharp turns
        if (random() > 0.85) {
            angle += random(-1, 1);
        }
    }

    return points;
}

function getDeKooningColor() {
    // De Kooning's palette: flesh tones, yellows, reds, blacks, whites
    const colors = [
        [255, 200, 170],  // Flesh pink
        [255, 220, 180],  // Pale flesh
        [240, 200, 100],  // Yellow ochre
        [220, 80, 60],    // Cadmium red
        [60, 60, 80],     // Dark blue-black
        [250, 245, 240],  // Off-white
        [180, 140, 100],  // Raw sienna
        [255, 100, 80],   // Vermillion
        [100, 120, 140],  // Steel blue
    ];
    return colors[floor(random(colors.length))];
}

function draw() {
    // Base layer - gestural ground
    noStroke();
    fill(235, 225, 210, 100);
    rect(0, 0, width, height);

    // Draw strokes in layers
    for (let s of strokes) {
        stroke(s.color[0], s.color[1], s.color[2], s.alpha);
        strokeWeight(s.weight);
        strokeCap(SQUARE);
        noFill();

        beginShape();
        for (let p of s.points) {
            // Add paint texture variation
            curveVertex(p.x + random(-3, 3), p.y + random(-3, 3));
        }
        endShape();

        // Secondary stroke for paint buildup effect
        if (random() > 0.5) {
            stroke(s.color[0], s.color[1], s.color[2], s.alpha * 0.3);
            strokeWeight(s.weight * 1.3);
            beginShape();
            for (let p of s.points) {
                curveVertex(p.x + random(-5, 5), p.y + random(-5, 5));
            }
            endShape();
        }
    }

    // Scraping/erasing effect
    for (let i = 0; i < 10; i++) {
        let x = random(width);
        let y = random(height);
        stroke(245, 240, 235, 100);
        strokeWeight(random(20, 40));
        line(x, y, x + random(-100, 100), y + random(-50, 50));
    }
}

function mousePressed() {
    background(245, 240, 235);
    generateStrokes();
    redraw();
}`
    },
    {
        id: 'escher-tessellation',
        name: 'Morphing Tessellation (Escher)',
        tags: ['tessellation', 'geometric', 'transformation'],
        code: `// Morphing Tessellation - Inspired by M.C. Escher
// Interlocking shapes that transform across the canvas
// Mathematical precision meets organic metamorphosis

let phase = 0;

function setup() {
    createCanvas(600, 600);
}

function draw() {
    background(250, 248, 245);

    const cols = 8;
    const rows = 8;
    const cellW = width / cols;
    const cellH = height / rows;

    for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
            let x = col * cellW;
            let y = row * cellH;

            // Transformation factor based on position
            let morphFactor = map(row, 0, rows - 1, 0, 1);
            morphFactor = (morphFactor + sin(phase + col * 0.3) * 0.2);
            morphFactor = constrain(morphFactor, 0, 1);

            // Alternate colors like Escher's day/night
            let isLight = (col + row) % 2 === 0;

            push();
            translate(x + cellW / 2, y + cellH / 2);

            // Draw morphing shape
            drawMorphingTile(cellW, cellH, morphFactor, isLight);
            pop();
        }
    }

    phase += 0.02;
}

function drawMorphingTile(w, h, morph, isLight) {
    // Interpolate between geometric and organic
    let c1 = isLight ? color(30, 35, 45) : color(245, 242, 235);
    let c2 = isLight ? color(245, 242, 235) : color(30, 35, 45);

    fill(c1);
    noStroke();

    beginShape();

    // Top edge - morphs from straight to wave
    let steps = 10;
    for (let i = 0; i <= steps; i++) {
        let px = map(i, 0, steps, -w/2, w/2);
        let py = -h/2;

        // Add wave based on morph factor
        py += sin(i / steps * PI * 2 + phase) * (h * 0.15 * morph);

        vertex(px, py);
    }

    // Right edge
    for (let i = 0; i <= steps; i++) {
        let px = w/2;
        let py = map(i, 0, steps, -h/2, h/2);

        // Bulge effect
        px += sin(i / steps * PI) * (w * 0.2 * morph);

        vertex(px, py);
    }

    // Bottom edge - inverse wave
    for (let i = steps; i >= 0; i--) {
        let px = map(i, 0, steps, -w/2, w/2);
        let py = h/2;

        py -= sin(i / steps * PI * 2 + phase) * (h * 0.15 * morph);

        vertex(px, py);
    }

    // Left edge
    for (let i = steps; i >= 0; i--) {
        let px = -w/2;
        let py = map(i, 0, steps, -h/2, h/2);

        px -= sin(i / steps * PI) * (w * 0.2 * morph);

        vertex(px, py);
    }

    endShape(CLOSE);

    // Add internal detail as morph increases
    if (morph > 0.3) {
        fill(c2);
        let detailSize = w * 0.15 * morph;

        // Eye-like detail (bird/fish motif)
        ellipse(w * 0.1, -h * 0.1, detailSize, detailSize * 0.6);

        // Fin/wing suggestion
        if (morph > 0.6) {
            noFill();
            stroke(c2);
            strokeWeight(1);
            arc(-w * 0.1, h * 0.1, detailSize * 2, detailSize, 0, PI);
        }
    }
}`
    }
];

// ============================================================================
// Gallery State
// ============================================================================

let editor = null;
let currentSketchIndex = 0;
let currentP5Instance = null;
let debounceTimer = null;
let isCodeVisible = true;
let carouselOffset = 0;

// DOM Elements
let codePanel, canvasContainer, errorDisplay, sketchNameEl, editorStatus;
let toggleCodeBtn, toggleCodeText, resetBtn;
let carouselTrack, carouselPrev, carouselNext;

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initElements();
    initEditor();
    initCarousel();
    initEventListeners();
    loadSketch(0);
});

function initElements() {
    codePanel = document.getElementById('code-panel');
    canvasContainer = document.getElementById('canvas-container');
    errorDisplay = document.getElementById('error-display');
    sketchNameEl = document.getElementById('sketch-name');
    editorStatus = document.getElementById('editor-status');
    toggleCodeBtn = document.getElementById('toggle-code-btn');
    toggleCodeText = document.getElementById('toggle-code-text');
    resetBtn = document.getElementById('reset-btn');
    carouselTrack = document.getElementById('carousel-track');
    carouselPrev = document.getElementById('carousel-prev');
    carouselNext = document.getElementById('carousel-next');
}

// ============================================================================
// CodeMirror Editor
// ============================================================================

function initEditor() {
    const editorElement = document.getElementById('code-editor');

    // p5.js autocomplete
    const p5Completions = autocompletion({
        override: [p5AutoComplete]
    });

    // Simple JS linter using Function constructor
    // NOTE: This is intentional for a live code editor - same pattern as CodePen/Shadertoy
    const jsLinter = linter(view => {
        const diagnostics = [];
        const code = view.state.doc.toString();

        try {
            // Basic syntax check - this is safe as we're only parsing, not executing
            Function('"use strict";' + code);
        } catch (e) {
            // Extract line number from error if possible
            const match = e.message.match(/line (\d+)/i);
            const line = match ? parseInt(match[1]) - 1 : 0;
            const lineStart = view.state.doc.line(Math.min(line + 1, view.state.doc.lines)).from;

            diagnostics.push({
                from: lineStart,
                to: lineStart + 1,
                severity: 'error',
                message: e.message
            });
        }

        return diagnostics;
    });

    editor = new EditorView({
        doc: '',
        extensions: [
            basicSetup,
            javascript(),
            oneDark,
            p5Completions,
            lintGutter(),
            jsLinter,
            EditorView.updateListener.of(update => {
                if (update.docChanged) {
                    scheduleExecution();
                }
            })
        ],
        parent: editorElement
    });
}

// p5.js autocomplete provider
function p5AutoComplete(context) {
    const word = context.matchBefore(/\w*/);
    if (!word || (word.from === word.to && !context.explicit)) return null;

    const p5Functions = [
        // Setup & Structure
        { label: 'setup', type: 'function', info: 'Called once at program start' },
        { label: 'draw', type: 'function', info: 'Called continuously after setup' },
        { label: 'createCanvas', type: 'function', info: 'Creates a canvas element' },
        { label: 'background', type: 'function', info: 'Sets the background color' },
        { label: 'frameRate', type: 'function', info: 'Sets the frame rate' },
        { label: 'noLoop', type: 'function', info: 'Stops draw() from looping' },
        { label: 'loop', type: 'function', info: 'Resumes draw() looping' },
        { label: 'push', type: 'function', info: 'Saves current drawing style' },
        { label: 'pop', type: 'function', info: 'Restores saved drawing style' },

        // Shapes
        { label: 'ellipse', type: 'function', info: 'Draws an ellipse' },
        { label: 'circle', type: 'function', info: 'Draws a circle' },
        { label: 'rect', type: 'function', info: 'Draws a rectangle' },
        { label: 'square', type: 'function', info: 'Draws a square' },
        { label: 'line', type: 'function', info: 'Draws a line' },
        { label: 'point', type: 'function', info: 'Draws a point' },
        { label: 'triangle', type: 'function', info: 'Draws a triangle' },
        { label: 'quad', type: 'function', info: 'Draws a quadrilateral' },
        { label: 'arc', type: 'function', info: 'Draws an arc' },
        { label: 'bezier', type: 'function', info: 'Draws a bezier curve' },
        { label: 'vertex', type: 'function', info: 'Adds a vertex to a shape' },
        { label: 'beginShape', type: 'function', info: 'Begins recording vertices' },
        { label: 'endShape', type: 'function', info: 'Ends recording vertices' },

        // Color
        { label: 'fill', type: 'function', info: 'Sets the fill color' },
        { label: 'noFill', type: 'function', info: 'Disables filling shapes' },
        { label: 'stroke', type: 'function', info: 'Sets the stroke color' },
        { label: 'noStroke', type: 'function', info: 'Disables strokes' },
        { label: 'strokeWeight', type: 'function', info: 'Sets stroke thickness' },
        { label: 'colorMode', type: 'function', info: 'Sets color mode (RGB/HSB)' },

        // Transform
        { label: 'translate', type: 'function', info: 'Moves the origin' },
        { label: 'rotate', type: 'function', info: 'Rotates the canvas' },
        { label: 'scale', type: 'function', info: 'Scales the canvas' },

        // Math
        { label: 'random', type: 'function', info: 'Returns a random number' },
        { label: 'noise', type: 'function', info: 'Returns Perlin noise value' },
        { label: 'map', type: 'function', info: 'Maps a value between ranges' },
        { label: 'constrain', type: 'function', info: 'Constrains a value' },
        { label: 'lerp', type: 'function', info: 'Linear interpolation' },
        { label: 'dist', type: 'function', info: 'Distance between points' },
        { label: 'sin', type: 'function', info: 'Sine function' },
        { label: 'cos', type: 'function', info: 'Cosine function' },
        { label: 'tan', type: 'function', info: 'Tangent function' },
        { label: 'abs', type: 'function', info: 'Absolute value' },
        { label: 'sqrt', type: 'function', info: 'Square root' },
        { label: 'pow', type: 'function', info: 'Power function' },
        { label: 'floor', type: 'function', info: 'Rounds down' },
        { label: 'ceil', type: 'function', info: 'Rounds up' },
        { label: 'round', type: 'function', info: 'Rounds to nearest' },

        // Constants
        { label: 'PI', type: 'constant', info: '3.14159...' },
        { label: 'TWO_PI', type: 'constant', info: '2 * PI' },
        { label: 'HALF_PI', type: 'constant', info: 'PI / 2' },
        { label: 'width', type: 'variable', info: 'Canvas width' },
        { label: 'height', type: 'variable', info: 'Canvas height' },
        { label: 'frameCount', type: 'variable', info: 'Number of frames drawn' },
        { label: 'mouseX', type: 'variable', info: 'Mouse X position' },
        { label: 'mouseY', type: 'variable', info: 'Mouse Y position' },

        // Pixels
        { label: 'loadPixels', type: 'function', info: 'Loads pixel data' },
        { label: 'updatePixels', type: 'function', info: 'Updates pixel data' },
        { label: 'pixels', type: 'variable', info: 'Pixel array' },
        { label: 'pixelDensity', type: 'function', info: 'Sets pixel density' },

        // Modes
        { label: 'rectMode', type: 'function', info: 'Sets rectangle mode' },
        { label: 'ellipseMode', type: 'function', info: 'Sets ellipse mode' },
        { label: 'CENTER', type: 'constant', info: 'Center mode' },
        { label: 'CORNER', type: 'constant', info: 'Corner mode' },
        { label: 'CORNERS', type: 'constant', info: 'Corners mode' },
        { label: 'CLOSE', type: 'constant', info: 'Close shape' },
        { label: 'HSB', type: 'constant', info: 'HSB color mode' },
        { label: 'RGB', type: 'constant', info: 'RGB color mode' }
    ];

    return {
        from: word.from,
        options: p5Functions.filter(f =>
            f.label.toLowerCase().startsWith(word.text.toLowerCase())
        )
    };
}

// ============================================================================
// Sketch Execution
// ============================================================================

function scheduleExecution() {
    clearTimeout(debounceTimer);
    editorStatus.textContent = 'Typing...';
    editorStatus.className = 'editor-status';

    debounceTimer = setTimeout(() => {
        executeSketch();
    }, 300);
}

function executeSketch() {
    const code = editor.state.doc.toString();

    // Clear previous instance
    if (currentP5Instance) {
        currentP5Instance.remove();
        currentP5Instance = null;
    }

    // Clear error display
    errorDisplay.classList.remove('visible');
    errorDisplay.innerHTML = '';

    try {
        // Create a sketch function from the code
        const sketchFn = createSketchFunction(code);

        // Create new p5 instance
        currentP5Instance = new p5(sketchFn, canvasContainer);

        editorStatus.textContent = 'Running';
        editorStatus.className = 'editor-status running';
    } catch (e) {
        showError(e);
    }
}

/**
 * Creates a p5.js instance-mode sketch function from global-mode user code.
 * This uses dynamic function creation intentionally - it's the standard pattern
 * for live code editors like CodePen, Shadertoy, p5.js Web Editor, etc.
 */
function createSketchFunction(code) {
    return function(p) {
        // Static p5 methods to bind
        const methods = [
            'createCanvas', 'background', 'fill', 'noFill', 'stroke', 'noStroke',
            'strokeWeight', 'ellipse', 'circle', 'rect', 'square', 'line', 'point',
            'triangle', 'quad', 'arc', 'bezier', 'vertex', 'beginShape', 'endShape',
            'push', 'pop', 'translate', 'rotate', 'scale', 'random', 'noise',
            'map', 'constrain', 'lerp', 'dist', 'sin', 'cos', 'tan', 'abs', 'sqrt',
            'pow', 'floor', 'ceil', 'round', 'colorMode', 'frameRate', 'noLoop', 'loop',
            'loadPixels', 'updatePixels', 'pixelDensity', 'rectMode', 'ellipseMode',
            'text', 'textSize', 'textAlign', 'textFont', 'image', 'loadImage',
            'noiseSeed', 'randomSeed', 'millis', 'second', 'minute', 'hour',
            'color', 'lerpColor', 'red', 'green', 'blue', 'alpha', 'hue', 'saturation', 'brightness',
            'curveVertex', 'bezierVertex', 'quadraticVertex', 'strokeCap', 'strokeJoin',
            'redraw', 'save', 'saveCanvas', 'createGraphics'
        ];

        // Static constants
        const constants = [
            'PI', 'TWO_PI', 'HALF_PI', 'QUARTER_PI', 'TAU',
            'CENTER', 'CORNER', 'CORNERS', 'RADIUS',
            'CLOSE', 'OPEN', 'CHORD', 'PIE',
            'HSB', 'RGB', 'HSL',
            'SQUARE', 'PROJECT', 'ROUND', 'MITER', 'BEVEL'
        ];

        // Build method bindings
        let fnBody = methods.map(m => `var ${m} = p.${m} ? p.${m}.bind(p) : undefined;`).join('\n');

        // Add constant bindings
        fnBody += '\n' + constants.map(c => `var ${c} = p.${c};`).join('\n');

        // Add dynamic property getters (these change during execution)
        // Using Object.defineProperties on a proxy object to avoid conflicts
        fnBody += `
            var __props = {};
            Object.defineProperties(__props, {
                width: { get: function() { return p.width; } },
                height: { get: function() { return p.height; } },
                frameCount: { get: function() { return p.frameCount; } },
                mouseX: { get: function() { return p.mouseX; } },
                mouseY: { get: function() { return p.mouseY; } },
                pmouseX: { get: function() { return p.pmouseX; } },
                pmouseY: { get: function() { return p.pmouseY; } },
                pixels: { get: function() { return p.pixels; }, set: function(v) { p.pixels = v; } },
                mouseIsPressed: { get: function() { return p.mouseIsPressed; } },
                keyIsPressed: { get: function() { return p.keyIsPressed; } },
                key: { get: function() { return p.key; } },
                keyCode: { get: function() { return p.keyCode; } }
            });
            var width = 0, height = 0, frameCount = 0, mouseX = 0, mouseY = 0;
            var pmouseX = 0, pmouseY = 0, pixels = [], mouseIsPressed = false;
            var keyIsPressed = false, key = '', keyCode = 0;
        `;

        // Wrap user code to update dynamic vars before each function call
        fnBody += `
            var __userSetup, __userDraw;

            ${code}

            if (typeof setup === 'function') {
                __userSetup = setup;
                p.setup = function() {
                    width = p.width; height = p.height; frameCount = p.frameCount;
                    mouseX = p.mouseX; mouseY = p.mouseY;
                    __userSetup();
                };
            }
            if (typeof draw === 'function') {
                __userDraw = draw;
                p.draw = function() {
                    width = p.width; height = p.height; frameCount = p.frameCount;
                    mouseX = p.mouseX; mouseY = p.mouseY;
                    pmouseX = p.pmouseX; pmouseY = p.pmouseY;
                    mouseIsPressed = p.mouseIsPressed;
                    keyIsPressed = p.keyIsPressed; key = p.key; keyCode = p.keyCode;
                    pixels = p.pixels;
                    __userDraw();
                };
            }
            if (typeof preload === 'function') p.preload = preload;
            if (typeof mousePressed === 'function') {
                var __userMousePressed = mousePressed;
                p.mousePressed = function() {
                    mouseX = p.mouseX; mouseY = p.mouseY;
                    __userMousePressed();
                };
            }
            if (typeof mouseReleased === 'function') p.mouseReleased = mouseReleased;
            if (typeof mouseMoved === 'function') p.mouseMoved = mouseMoved;
            if (typeof mouseDragged === 'function') p.mouseDragged = mouseDragged;
            if (typeof keyPressed === 'function') p.keyPressed = keyPressed;
            if (typeof keyReleased === 'function') p.keyReleased = keyReleased;
        `;

        // Intentional use of Function constructor for live code execution
        // This is client-side only and matches industry-standard creative coding tools
        Function('p', fnBody)(p);
    };
}

function showError(error) {
    editorStatus.textContent = 'Error';
    editorStatus.className = 'editor-status error';

    errorDisplay.innerHTML = `<pre>${escapeHtml(error.message)}</pre>`;
    errorDisplay.classList.add('visible');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// Carousel
// ============================================================================

function initCarousel() {
    // Generate thumbnails for each sketch
    SKETCHES.forEach((sketch, index) => {
        const thumb = createThumbnail(sketch, index);
        carouselTrack.appendChild(thumb);
    });

    updateCarouselButtons();
}

function createThumbnail(sketch, index) {
    const thumb = document.createElement('div');
    thumb.className = 'carousel-thumbnail';
    thumb.dataset.index = index;

    // Create a mini canvas for the thumbnail
    const canvas = document.createElement('canvas');
    canvas.width = 80;
    canvas.height = 60;
    thumb.appendChild(canvas);

    // Label
    const label = document.createElement('div');
    label.className = 'thumb-label';
    label.textContent = sketch.name;
    thumb.appendChild(label);

    // Click handler
    thumb.addEventListener('click', () => {
        loadSketch(index);
    });

    // Render thumbnail preview (delayed to not block initial load)
    setTimeout(() => renderThumbnail(sketch, canvas), 100 * index);

    return thumb;
}

function renderThumbnail(sketch, canvas) {
    // Create a tiny p5 instance to render a preview
    const thumbSketch = (p) => {
        try {
            const fn = createSketchFunction(sketch.code);
            fn(p);

            // Override setup to use smaller canvas
            const originalSetup = p.setup;
            p.setup = function() {
                p.createCanvas(80, 60);
                p.scale(80 / 600, 60 / 600); // Scale down
                if (originalSetup) originalSetup.call(this);
            };
        } catch (e) {
            // Silently fail for thumbnails
            p.setup = () => {
                p.createCanvas(80, 60);
                p.background(30);
                p.fill(100);
                p.textAlign(p.CENTER, p.CENTER);
                p.textSize(8);
                p.text('Preview', 40, 30);
            };
        }
    };

    // Create instance, let it run for a few frames, then capture
    const tempContainer = document.createElement('div');
    tempContainer.style.position = 'absolute';
    tempContainer.style.left = '-9999px';
    document.body.appendChild(tempContainer);

    const instance = new p5(thumbSketch, tempContainer);

    setTimeout(() => {
        // Capture the canvas content
        const sourceCanvas = tempContainer.querySelector('canvas');
        if (sourceCanvas) {
            const ctx = canvas.getContext('2d');
            ctx.drawImage(sourceCanvas, 0, 0, 80, 60);
        }
        instance.remove();
        tempContainer.remove();
    }, 500);
}

function updateCarouselButtons() {
    const thumbWidth = 80 + 12; // width + gap
    const visibleWidth = carouselTrack.parentElement.offsetWidth;
    const totalWidth = SKETCHES.length * thumbWidth;
    const maxOffset = Math.max(0, totalWidth - visibleWidth);

    carouselPrev.disabled = carouselOffset <= 0;
    carouselNext.disabled = carouselOffset >= maxOffset;
}

function scrollCarousel(direction) {
    const thumbWidth = 80 + 12;
    const visibleWidth = carouselTrack.parentElement.offsetWidth;
    const scrollAmount = Math.floor(visibleWidth / thumbWidth) * thumbWidth;
    const totalWidth = SKETCHES.length * thumbWidth;
    const maxOffset = Math.max(0, totalWidth - visibleWidth);

    carouselOffset = Math.max(0, Math.min(maxOffset, carouselOffset + direction * scrollAmount));
    carouselTrack.style.transform = `translateX(-${carouselOffset}px)`;

    updateCarouselButtons();
}

function updateActiveThumbnail() {
    const thumbs = carouselTrack.querySelectorAll('.carousel-thumbnail');
    thumbs.forEach((thumb, index) => {
        thumb.classList.toggle('active', index === currentSketchIndex);
    });
}

// ============================================================================
// Sketch Loading
// ============================================================================

function loadSketch(index) {
    currentSketchIndex = index;
    const sketch = SKETCHES[index];

    // Update editor content
    editor.dispatch({
        changes: {
            from: 0,
            to: editor.state.doc.length,
            insert: sketch.code
        }
    });

    // Update UI
    sketchNameEl.textContent = sketch.name;
    updateActiveThumbnail();

    // Execute immediately
    executeSketch();
}

function resetSketch() {
    loadSketch(currentSketchIndex);
}

// ============================================================================
// Event Listeners
// ============================================================================

function initEventListeners() {
    // Toggle code panel
    toggleCodeBtn.addEventListener('click', () => {
        isCodeVisible = !isCodeVisible;
        codePanel.classList.toggle('collapsed', !isCodeVisible);
        document.getElementById('editor-area').classList.toggle('fullscreen', !isCodeVisible);
        toggleCodeText.textContent = isCodeVisible ? 'Hide Code' : 'Show Code';
    });

    // Reset button
    resetBtn.addEventListener('click', resetSketch);

    // Carousel navigation
    carouselPrev.addEventListener('click', () => scrollCarousel(-1));
    carouselNext.addEventListener('click', () => scrollCarousel(1));

    // Resize handle
    initResizeHandle();

    // Window resize
    window.addEventListener('resize', () => {
        updateCarouselButtons();
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Cmd/Ctrl + Enter to run
        if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
            e.preventDefault();
            executeSketch();
        }

        // Cmd/Ctrl + S to prevent default (no saving)
        if ((e.metaKey || e.ctrlKey) && e.key === 's') {
            e.preventDefault();
        }
    });
}

function initResizeHandle() {
    const resizeHandle = document.getElementById('resize-handle');
    let isResizing = false;
    let startX, startWidth;

    resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        startWidth = codePanel.offsetWidth;
        resizeHandle.classList.add('dragging');
        document.body.style.cursor = 'col-resize';
        e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;

        const diff = e.clientX - startX;
        const newWidth = Math.max(300, Math.min(window.innerWidth - 300, startWidth + diff));
        codePanel.style.width = `${newWidth}px`;
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            resizeHandle.classList.remove('dragging');
            document.body.style.cursor = '';
        }
    });
}
