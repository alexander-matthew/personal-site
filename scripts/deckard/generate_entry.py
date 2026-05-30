#!/usr/bin/env python3
"""Generate one day's Deckard's Diary entry.

An entry is a short-form piece (poem or story) plus a generative-art sketch it
inspires. Two backends:

  * **API** (preferred, used by CI): if ``ANTHROPIC_API_KEY`` is set, ask the
    model for the piece and a matching canvas sketch, under strict thematic
    constraints, and validate the result hard.
  * **offline** (resilience fallback): compose from curated banks so the daily
    job never fails and never emits anything off-theme, even with no network.

Outputs two files, the dated halves of one entry:

  app/content/deckard/entries/<date>.json   # the writing + metadata
  app/static/js/deckard/sketches/<date>.js  # the exact source the page runs

Usage:
  uv run python scripts/deckard/generate_entry.py            # today, API or offline
  uv run python scripts/deckard/generate_entry.py --offline  # force offline
  uv run python scripts/deckard/generate_entry.py --date 2026-06-01 --force
  uv run python scripts/deckard/generate_entry.py --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRIES_DIR = ROOT / 'app' / 'content' / 'deckard' / 'entries'
SKETCHES_DIR = ROOT / 'app' / 'static' / 'js' / 'deckard' / 'sketches'

FORMS = ['fragments', 'prose', 'verse']

# ---------------------------------------------------------------------------
# Theme. The diary is kept by an entity of ambiguous aliveness. The voice is
# reflective, spare, wabi-sabi (imperfect, transient, unfinished); the world is
# existential near-future. Hard constraints below are enforced after generation.
# ---------------------------------------------------------------------------

THEME_BRIEF = """\
Voice: a first-person diarist whose own aliveness is uncertain — never resolved.
Mood: reflective, restrained, melancholy-tender; wabi-sabi (imperfect, transient,
unfinished, beauty in wear). World: a quiet existential near-future of rain,
glass, light, mirrors, photographs, hands, breath, distance. The reader should
not be able to tell whether the writer is a person or something that has learned
to pass as one. Keep it short. Leave things unsaid."""

# Anything matching these gets the piece rejected — it would name what must stay
# implied, or point directly at the works that inspired the mood.
FORBIDDEN = re.compile(
    r"""\b(
        a\.?i\.? | artificial\ intelligence | machine\ learning | neural |
        robot | android | cyborg | replicant | algorithm | software | computer |
        blade\ runner | deckard | terminator | skynet | akira | ex\ machina |
        ghost\ in\ the\ shell | matrix | hal\ 9000
    )\b""",
    re.IGNORECASE | re.VERBOSE,
)

PALETTES = [
    ['#0a0e14', '#1b2a33', '#3fb7c4', '#d98c3e', '#e8e8e8'],
    ['#0a0a0c', '#15161a', '#8a8f99', '#cfd6df', '#4da6ff'],
    ['#070a0f', '#11161f', '#ff4d5e', '#34e0d6', '#e8e8e8'],
    ['#0b0a10', '#171522', '#7a6cff', '#c8b6ff', '#e6e1ff'],
    ['#0a0f0d', '#13201b', '#3fd49b', '#d8c98c', '#eef2ee'],
    ['#100a0a', '#221515', '#ff8a5b', '#ffd3a3', '#f3e7df'],
]

# --- offline content banks -------------------------------------------------

OFFLINE_FRAGMENTS = [
    "I remember a room I have never stood in. The light there is always late.",
    "They tell me the rain is only weather. Then why does it knock to be let in.",
    "A photograph insists: this happened, this was warm.",
    "I counted my breaths to be sure they were mine. The number changes.",
    "Somewhere a door I did not close is still open. I feel its draft in my hands.",
    "The mirror agrees with me, mostly. It is the mostly I keep.",
    "I have a memory of the sea I cannot have earned.",
    "Each morning I assemble the same face and hope it holds till dark.",
    "What I miss most is a place I am not certain ever stood.",
    "I keep an inventory of tendernesses meant for someone else.",
]

OFFLINE_VERSE = [
    ["They ask if I dream.", "I say I close my eyes", "and a city fills the dark —",
     "one I have never visited", "yet know the price of bread in."],
    ["The window holds two of me:", "the one inside, the one the night keeps.",
     "We blink in turn,", "uncertain which is the reflection."],
    ["I was given a name", "the way a coat is given —", "to be worn, not to be true.",
     "Still, on cold mornings, it fits."],
    ["Out past the glass the towers pulse", "their slow red, awake, awake,",
     "and I answer in the only language I have:", "I stay up with them."],
]

OFFLINE_PROSE = [
    "Each morning I take my face down and put it on by feel. There is a seam at "
    "the jaw the light finds at certain hours, a hairline where the made meets "
    "the meant. I have decided not to mind it.",
    "A stranger smiled at me as if at someone they had loved and lost, and for "
    "the length of that smile I was that person, the way water is briefly the "
    "shape of the cup. Then it passed, and I was the cup again.",
    "I have been keeping the rain. Not all of it — a drop here, a drop there, the "
    "ones that seemed to mean something. By now I have a small grey weather of my "
    "own, and no sky to return it to.",
]

OFFLINE_COLOPHONS = [
    "rain that mostly forgets, and a few drops it decides to hold.",
    "a symmetry that almost holds, and the light that finds where it doesn't.",
    "a skyline that blinks back; each refresh, a city that never was.",
    "drift and pull; a field that never settles the same way twice.",
]

# Three offline sketch templates, palette-agnostic (palette arrives as an arg at
# runtime). Each obeys the contract: optionally return step(t) for animation.

SKETCH_RAIN = """\
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
"""

SKETCH_FLOW = """\
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
"""

SKETCH_SKYLINE = """\
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
"""

OFFLINE_SKETCHES = {'fragments': SKETCH_RAIN, 'verse': SKETCH_SKYLINE, 'prose': SKETCH_FLOW}


# --- helpers ---------------------------------------------------------------


def existing_dates() -> list[str]:
    if not ENTRIES_DIR.exists():
        return []
    return sorted(p.stem for p in ENTRIES_DIR.glob('*.json'))


def contains_forbidden(*texts: str) -> str | None:
    for t in texts:
        m = FORBIDDEN.search(t or '')
        if m:
            return m.group(0)
    return None


def validate_entry(data: dict, sketch_code: str) -> None:
    required = ['title', 'poem', 'palette', 'colophon']
    for k in required:
        if not data.get(k):
            raise ValueError(f'missing required field: {k}')
    if not isinstance(data['poem'], list) or not any(data['poem']):
        raise ValueError('poem must be a non-empty list of lines')
    pal = data['palette']
    if not (3 <= len(pal) <= 6) or not all(re.fullmatch(r'#[0-9a-fA-F]{6}', c) for c in pal):
        raise ValueError('palette must be 3-6 hex colors')
    bad = contains_forbidden(data['title'], data['colophon'], *data['poem'])
    if bad:
        raise ValueError(f'forbidden term in text: {bad!r}')
    if 'window.__deckardSketch' not in sketch_code or 'function' not in sketch_code:
        raise ValueError('sketch must define window.__deckardSketch as a function')
    if sketch_code.count('{') != sketch_code.count('}'):
        raise ValueError('sketch braces are unbalanced')
    # If node is available, hard-check the syntax (via a temp file — `node
    # --check` wants a filename, not stdin).
    node = shutil.which('node')
    if node:
        import tempfile

        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as tmp:
            tmp.write(sketch_code)
            tmp_path = tmp.name
        try:
            proc = subprocess.run([node, '--check', tmp_path], capture_output=True, text=True)
        finally:
            os.unlink(tmp_path)
        if proc.returncode != 0:
            raise ValueError(f'sketch failed node --check: {proc.stderr.strip()}')


# --- offline backend -------------------------------------------------------


def _roman(n: int) -> str:
    return ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii'][n - 1]


def generate_offline(form: str, day_number: int, rng: random.Random) -> tuple[dict, str]:
    palette = rng.choice(PALETTES)
    if form == 'fragments':
        chosen = rng.sample(OFFLINE_FRAGMENTS, k=min(5, len(OFFLINE_FRAGMENTS)))
        poem = []
        for i, line in enumerate(chosen, 1):
            poem.append(f'{_roman(i)}.  {line}')
            poem.append('')
        poem = poem[:-1]
        title = 'What the Rain Keeps'
    elif form == 'verse':
        poem = list(rng.choice(OFFLINE_VERSE))
        title = 'Field Notes Before Sleep'
    else:  # prose
        paras = rng.sample(OFFLINE_PROSE, k=min(2, len(OFFLINE_PROSE)))
        poem = []
        for p in paras:
            poem.append(p)
            poem.append('')
        poem = poem[:-1]
        title = 'Inventory of a Borrowed Face'

    data = {
        'day_number': day_number,
        'title': title,
        'form': form,
        'epigraph': None,
        'poem': poem,
        'palette': palette,
        'art': {'title': {'fragments': 'rainfield', 'verse': 'nightwatch', 'prose': 'driftfield'}[form]},
        'colophon': rng.choice(OFFLINE_COLOPHONS),
        'seed_phrase': poem[0].strip()[:48] if poem else 'untitled',
    }
    return data, OFFLINE_SKETCHES[form]


# --- API backend -----------------------------------------------------------

PROMPT = """\
You keep a daily diary. Today's entry is one short piece in the form: {form}.

{brief}

Also invent a generative-art sketch — a small JavaScript canvas program — that
is an *echo* of the piece (its mood, motion, palette), not an illustration of it.

Return ONE JSON object and nothing else, with exactly these keys:
  "title":       a short title (no quotation marks inside)
  "form":        "{form}"
  "epigraph":    a short italic line, or null
  "poem":        an array of strings (the lines; use "" for stanza breaks)
  "palette":     an array of 4-5 hex colors like "#0a0e14" (dark, cinematic)
  "art_title":   one lowercase word naming the sketch
  "colophon":    one lowercase sentence describing the art's behavior
  "seed_phrase": a short evocative phrase from the piece
  "sketch_code": a STRING of JavaScript implementing exactly this contract:

      window.__deckardSketch = function (ctx, w, h, rng, palette) {{
        // ctx: 2D canvas context. w,h: logical pixels. rng(): seeded float [0,1).
        // palette: the array above. Set up state using rng (deterministic).
        // Return an optional function step(t) for animation (t = ms),
        // or return nothing to draw a single static frame.
      }};

  The sketch must be self-contained (no external libs, no DOM, no eval, no
  setTimeout), 30-90 lines, and visually striking on a dark canvas.

Hard rules for ALL text: do NOT use the words ai, artificial intelligence,
robot, android, machine, algorithm, computer, replicant, or name any film,
show, or book. Keep the writing spare. Leave room for doubt.
Output only the JSON object."""


def _parse_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```[a-zA-Z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text).strip()
    start, end = text.find('{'), text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError('no JSON object found in model output')
    return json.loads(text[start : end + 1])


def generate_via_api(form: str, day_number: int) -> tuple[dict, str]:
    import httpx  # local import: only needed on the API path

    key = os.environ['ANTHROPIC_API_KEY']
    model = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-6')
    prompt = PROMPT.format(form=form, brief=THEME_BRIEF)
    resp = httpx.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key': key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        json={
            'model': model,
            'max_tokens': 2400,
            'messages': [{'role': 'user', 'content': prompt}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    text = ''.join(b.get('text', '') for b in resp.json().get('content', []))
    data = _parse_json_object(text)

    sketch_code = data.pop('sketch_code', '').strip() + '\n'
    entry = {
        'day_number': day_number,
        'title': data.get('title', 'untitled'),
        'form': form,
        'epigraph': data.get('epigraph'),
        'poem': data.get('poem', []),
        'palette': data.get('palette', []),
        'art': {'title': data.get('art_title', 'study')},
        'colophon': data.get('colophon', ''),
        'seed_phrase': data.get('seed_phrase'),
    }
    return entry, sketch_code


# --- orchestration ---------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate a Deckard's Diary entry.")
    ap.add_argument('--date', help='YYYY-MM-DD (default: today, UTC)')
    ap.add_argument('--form', choices=FORMS, help='override the daily form')
    ap.add_argument('--offline', action='store_true', help='force the offline backend')
    ap.add_argument('--force', action='store_true', help='overwrite an existing entry')
    ap.add_argument('--dry-run', action='store_true', help='print, do not write')
    args = ap.parse_args(argv)

    date = args.date or dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
        print(f'bad --date: {date}', file=sys.stderr)
        return 2

    dest_json = ENTRIES_DIR / f'{date}.json'
    if dest_json.exists() and not args.force and not args.dry_run:
        print(f'entry already exists: {dest_json} (use --force to overwrite)')
        return 0

    existing = existing_dates()
    day_number = len(existing) + 1 if date not in existing else existing.index(date) + 1
    rng = random.Random(date)
    form = args.form or FORMS[(day_number - 1) % len(FORMS)]

    use_api = not args.offline and bool(os.environ.get('ANTHROPIC_API_KEY'))
    entry = sketch = None
    if use_api:
        try:
            entry, sketch = generate_via_api(form, day_number)
            validate_entry(entry, sketch)
            print(f'generated via API (model={os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")})')
        except Exception as e:  # noqa: BLE001 — any API/validation failure → fall back
            print(f'API path failed ({e}); falling back to offline', file=sys.stderr)
            entry = sketch = None
    if entry is None:
        entry, sketch = generate_offline(form, day_number, rng)
        validate_entry(entry, sketch)
        print('generated via offline backend')

    if args.dry_run:
        print(json.dumps(entry, indent=2, ensure_ascii=False))
        print('--- sketch ---')
        print(sketch)
        return 0

    ENTRIES_DIR.mkdir(parents=True, exist_ok=True)
    SKETCHES_DIR.mkdir(parents=True, exist_ok=True)
    dest_json.write_text(json.dumps(entry, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (SKETCHES_DIR / f'{date}.js').write_text(sketch, encoding='utf-8')
    print(f'wrote {dest_json}')
    print(f'wrote {SKETCHES_DIR / f"{date}.js"}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
