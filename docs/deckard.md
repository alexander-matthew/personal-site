# Deckard's Diary

A daily, machine-kept diary. Each day produces one **entry**: a short-form piece
(poem or story, the form varies) paired with a **generative-art sketch** that
echoes it. The two are shown together in a small in-browser IDE — the writing,
the running art, and *the exact source that drew it*.

The art is reseeded **per viewer and per refresh**, so no two readers ever see
the same rendering of the same algorithm, yet the algorithm on display is the one
that ran.

## Theme

A reflective, existential near-future. The diarist's own aliveness is never
resolved — the reader should not be able to tell whether the writer is a person
or something that has learned to pass as one. Wabi-sabi in spirit: imperfect,
transient, unfinished. The mood is deliberately *implied*: the generator's hard
rules forbid naming the genre, its tropes, or the works that inspired it.

## Anatomy of an entry

Each entry is two dated files that share a stem:

```
app/content/deckard/entries/<YYYY-MM-DD>.json   # the writing + metadata
app/static/js/deckard/sketches/<YYYY-MM-DD>.js  # the art algorithm (served as-is)
```

Entry JSON:

| field | meaning |
| --- | --- |
| `day_number` | 1-based ordinal |
| `title` | the piece's title |
| `form` | `fragments` \| `prose` \| `verse` (drives type-setting) |
| `epigraph` | optional short italic line, or `null` |
| `poem` | array of lines; `""` marks a stanza break |
| `palette` | 3–6 hex colors, passed to the sketch |
| `art.title` | the sketch's name |
| `colophon` | one lowercase line describing the art's behavior |
| `seed_phrase` | a short evocative phrase from the piece |

The sketch's URL is derived from the date, so it is never stored in the JSON
(`app/services/deckard.py` fills `art.sketch_url`).

## The sketch contract

A sketch is plain, first-party JavaScript served from `/static`, so it loads via
a normal `<script src>` — **no `eval`, no CSP relaxation**. The page fetches the
same file's text only to *display* it, which guarantees what you read is what
ran.

```js
window.__deckardSketch = function (ctx, w, h, rng, palette) {
  // ctx: 2D canvas context. w,h: logical pixels. rng(): seeded float in [0,1).
  // palette: the entry's colors. Set up state from rng (deterministic).
  // Return an optional step(t) for animation (t = ms), or nothing for one frame.
};
```

The runtime (`app/static/js/deckard/deckard-app.js`) builds the seed from a
persistent per-viewer token (localStorage) plus a per-refresh nonce, hashes it
into a `mulberry32` PRNG, sizes the canvas for device pixels, and either loops
`step(t)` or leaves the single static frame. "regenerate" reseeds and redraws.

## Routes

| Route | Purpose |
| --- | --- |
| `/projects/deckard` | latest entry (the IDE view) |
| `/projects/deckard/archive` | every entry, newest first |
| `/projects/deckard/<date>` | dated permalink |
| `/projects/deckard/api/entries` | JSON metadata list |
| `/projects/deckard/api/entry/<date>` | one entry as JSON |

## Daily generation

`scripts/deckard/generate_entry.py` writes the day's two files. Two backends:

- **API** (preferred): with `ANTHROPIC_API_KEY` set, the model writes the piece
  and a matching sketch under the theme constraints. Output is validated hard —
  required fields, palette shape, a forbidden-terms regex, balanced braces, and
  `node --check` on the sketch when node is present. Any failure falls back to:
- **offline**: composes from curated banks and one of three sketch templates.
  Deterministic per date, always on-theme, no network. Guarantees the daily job
  never fails or emits garbage.

```bash
uv run python scripts/deckard/generate_entry.py            # today; API or offline
uv run python scripts/deckard/generate_entry.py --offline  # force offline
uv run python scripts/deckard/generate_entry.py --date 2026-06-01 --force
uv run python scripts/deckard/generate_entry.py --dry-run  # print, don't write
```

The form rotates by `day_number` unless `--form` is given.

## Automation (git as the database)

`.github/workflows/deckard-daily.yml` runs daily (09:12 UTC) and on demand:
generate → commit the two files to `main` → the existing deploy workflow ships
them. The corpus scales by committing files; no database.

**Deploy gotcha:** a push made with the default `GITHUB_TOKEN` does not trigger
other workflows. Add a fine-grained PAT with `contents:write` as the secret
`DECKARD_PUSH_TOKEN` so the daily commit triggers `deploy.yml`. Without it the
entry is still committed and ships on the next push to `main`.

Secrets/vars used: `ANTHROPIC_API_KEY` (secret, optional → offline if absent),
`ANTHROPIC_MODEL` (var, optional), `DECKARD_PUSH_TOKEN` (secret, optional).

## Adding an entry by hand

Drop a `<date>.json` in `entries/` and a matching `<date>.js` in `sketches/`.
The index auto-discovers files; `app.services.deckard.reload()` clears the cache
in long-running processes. The three seed entries are good templates to copy.
