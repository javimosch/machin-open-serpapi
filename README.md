# open-serpapi

An OSS, agent-first, self-hostable alternative to [SerpApi](https://serpapi.com) —
a single native binary written in **[machin](https://github.com/javimosch/machin)** (MFL).

SerpApi sells three layers: **fetch** (get past blocking), **parse** (messy SERP
HTML/JSON → clean structure), and **schema** (a stable JSON contract agents code
against). The fetch layer is a proxy/CAPTCHA arms race you can't win self-hosted —
so open-serpapi doesn't try. It owns **parse + schema**, and makes **fetch a plugin**:

```
<any fetcher> "query"  |  open-serpapi parse --engine google_maps  ->  SerpApi JSON
```

Because the binary never touches the network, it has **no TLS dependency**, is
**fully deterministic**, and is **offline-testable** against saved raw fixtures.
Fetch (proxies, browsers, API keys) is decoupled and swappable — see
[`fetchers/`](fetchers/README.md).

## Why

- **Self-host, no per-query bill, no vendor lock** — your queries never leave your box.
- **Agent-first** — clean JSON over a unix pipe; drop it behind any agent/tool.
- **One static binary** — no Node, no ORM, no Python, no Docker required.
- **Decoupled fetch/parse** — cleaner than SerpApi's monolith; bring your own scraper.

## Status

Early but real. Seven engines:

- **`google`** — rendered SERP **HTML** → `organic_results[]` (`position`,
  `title`, `link`, `displayed_link`, `snippet`). A small HTML tokenizer in MFL
  that anchors on *structure* (each result is an `<h3>` wrapped by an external
  `<a href>`, with `<cite>` + snippet), so it survives Google's randomized class
  names. Decodes `/url?q=` redirects, unescapes HTML entities, filters
  People-Also-Ask / internal links. `displayed_link` is hardened against
  real-HTML variety: it picks the `<cite>` that matches the result's host and
  falls back to the bare domain for result types (Quora, Medium) whose only
  cites are metadata ("4 months ago"). Verified on live SERP HTML — 12/12
  results with correct links + display links.
- **`google_maps`** — raw record array → `local_results[]` (`title`, `rating`,
  `reviews`, `type`, `address`, `phone`, `website`, `gps_coordinates`,
  `place_id`, `maps_url`) — actionable rows for outreach/lead lists.
- **`duckduckgo`**, **`bing`**, **`startpage`** & **`brave`** — **defined as pure
  JSON, no MFL.** A tiny CSS-selector engine (`src/css.src`: HTML → DOM → selector
  matching) runs a declarative spec ([`engines/*.json`](engines/README.md)). All
  verified on live HTML (10–20 results each); Bing's base64 `ck/a` redirect links
  are decoded to real URLs, and the runner skips non-result blocks (e.g. a
  Startpage knowledge panel) whose identity field is empty. Adding a clean-markup
  engine is a JSON file, not code.

- **`linkedin`** — **authed** LinkedIn HTML → `posts[]` with nested `comments[]`.
  Two page shapes, auto-detected: content-**search** (obfuscated classes → anchor
  on stable *attributes* like `aria-label="Open control menu for post by …"`) and
  post-**detail** (classic semantic classes → `update-components-text`, and each
  comment via `comments-comment-meta__description-title` + `__main-content`).
  Each post: `author`, `author_url`, `author_type`, `text`, `hashtags`; each
  comment: `author`, `author_url`, `headline`, `text`. Verified on real logged-in
  HTML — 18/18 comments. Best driven by attaching to your own browser over CDP;
  see the [fetcher contract](fetchers/README.md). **Scraping logged-in LinkedIn
  violates their ToS and risks your account; personal, low-volume use only.**

Fetch stays out of scope by design — it's a [plugin](fetchers/README.md). An
anti-detect browser fetcher gets past CAPTCHA walls (verified live — 12 Google
organic results where curl/plain-puppeteer got only the CAPTCHA page); such
reference fetchers are maintained separately so the binary stays network-free.

> Snippets come back empty for `#:~:text=` highlight-style results — Google
> doesn't ship a snippet block for those in the server HTML (confirmed with a
> full DOM parser), so there's nothing to extract.

Roadmap: more declarative engines (Yandex, Mojeek, …), and a SQLite result cache.
Staying CLI agent-first — no SerpApi-parity server.

## Quick start

```bash
./build.sh                       # encode src/serpapi.src -> build, compile -> ./open-serpapi
MACHIN=~/ai/machin/machin ./build.sh   # against a local machin

# parse saved raw bytes (offline, no fetcher needed)
./open-serpapi parse --engine google      < fixtures/google/machin-lang.raw.html
./open-serpapi parse --engine google_maps < fixtures/google_maps/coworking-annecy.raw.json

# end-to-end: pipe ANY fetcher (a script that prints a page to stdout) into parse
<fetcher> "coworking annecy"          | ./open-serpapi parse --engine google_maps
<fetcher> "machin programming language" | ./open-serpapi parse --engine google
<fetcher> "machin programming language" | ./open-serpapi parse --engine duckduckgo   # or bing/startpage/brave
```

Output (SerpApi `google_maps` shape):

```json
{
  "search_metadata":   { "status": "Success", "engine": "google_maps" },
  "search_parameters": { "engine": "google_maps", "type": "search", "q": "coworking annecy" },
  "local_results": [
    { "position": 1, "title": "Cowork Annecy", "rating": 4.7, "reviews": 128,
      "type": "Coworking space", "address": "12 Rue Carnot, 74000 Annecy",
      "phone": "+33 4 50 00 00 00", "website": "https://cowork-annecy.fr" }
  ]
}
```

## Tests

Deterministic and offline — frozen raw fixtures diffed against golden JSON:

```bash
./test.sh
```

Add a case: drop `fixtures/<engine>/<name>.raw.json`, generate its golden with
`./open-serpapi parse --engine <engine> < that.raw.json | jq . > golden/<engine>/<name>.json`,
eyeball it, commit both. The corpus is the parser's spec; live scrapers only run
to *refresh* fixtures when a SERP's HTML drifts.

## Layout

```
src/serpapi.src     # core: bespoke parsers (google, google_maps) + schema + CLI
src/css.src         # HTML -> DOM + CSS-selector engine + spec runner + linkedin
skills/             # agent-loadable how-to guide (open-serpapi.md)
engines/<name>.json # declarative spec-driven engines (e.g. duckduckgo) + how-to
build.sh            # encode src/*.src -> .mfl -> native binary
fetchers/README.md  # the layer-1 plugin contract (fetchers maintained separately)
fixtures/<engine>/  # frozen raw fetcher output (parser input)
golden/<engine>/    # expected output (parser spec)
test.sh             # run fixtures through the parser, diff goldens
```

## Agent skills

A self-contained, in-repo guide for agents driving open-serpapi —
[`skills/open-serpapi.md`](skills/open-serpapi.md) (the model, engines, schemas, adding an
engine, testing). The repo is self-documenting for any agent that clones it.

> **Fetchers live separately.** open-serpapi is pure parse + schema and never touches the
> network — layer-1 fetchers (web renderers, the authed LinkedIn/Reddit harvesters) are a
> swappable plugin, maintained outside this repo. See [`fetchers/README.md`](fetchers/README.md)
> for the contract.

## grepapi — the agent-first cloud on top

open-serpapi (the parser) + your own fetchers are **layer 1**.
**[grepapi](https://grepapi.intrane.fr)** is the brains on top — a **fat-client /
thin-server** control plane. You still run the fetchers **yourself** (BYO-browser, from
your own session — no proxy bill), and an **agentic onboarding** walks your agent/operator
through the setup. grepapi adds everything *above* the raw fetch:

- **Planner** — one ICP → the right queries per engine (web · Maps · Reddit · authed LinkedIn).
- **Scoring · qualification · cross-account dedup** — a data graph that kills job-boards & directories and de-dupes people and companies across runs.
- **Briefs + actions** — every lead ranked with the action to take (call · comment · reply · research) and a brief your own LLM turns into outreach (**BYO-LLM** — no token markup).
- **Workflow** — status, notes, retention, usage & billing.

CLI-first, agent-native (JSON + typed exit codes), **free tier**. You bring the browser and
the LLM; grepapi sells the brains, not the commodities. → **<https://grepapi.intrane.fr>**

## License

MIT.
