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

Early but real. Two engines:

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
- **`google_maps`** — raw record array → SerpApi `local_results[]`.
- **`duckduckgo`** & **`bing`** — **defined as pure JSON, no MFL.** A tiny
  CSS-selector engine (`src/css.src`: HTML → DOM → selector matching) runs a
  declarative spec ([`engines/*.json`](engines/README.md)). Both verified on live
  HTML — 10/10 results each; Bing's base64 `ck/a` redirect links are decoded to
  real URLs. Adding a clean-markup engine (Startpage, Brave, …) is now a JSON
  file, not code.

Fetch is solved at the agent-first level too: `fetchers/google.sh` drives the
Botasaurus anti-detect browser and **bypasses Google's CAPTCHA wall** (verified
live — 12 organic results where curl/plain-puppeteer got only the CAPTCHA page).

> Snippets come back empty for `#:~:text=` highlight-style results — Google
> doesn't ship a snippet block for those in the server HTML (confirmed with a
> full DOM parser), so there's nothing to extract.

Roadmap: more declarative engines (Bing, Startpage), and a SQLite result cache.
Staying CLI agent-first — no SerpApi-parity server.

## Quick start

```bash
./build.sh                       # encode src/serpapi.src -> build, compile -> ./open-serpapi
MACHIN=~/ai/machin/machin ./build.sh   # against a local machin

# parse saved raw bytes (offline, no fetcher needed)
./open-serpapi parse --engine google      < fixtures/google/machin-lang.raw.html
./open-serpapi parse --engine google_maps < fixtures/google_maps/coworking-annecy.raw.json

# end-to-end with a live fetcher plugin
./fetchers/google-maps.sh "coworking annecy" | ./open-serpapi parse --engine google_maps

# Google, past the CAPTCHA wall (Botasaurus anti-detect browser — verified live)
./fetchers/google.sh "machin programming language" | ./open-serpapi parse --engine google

# DuckDuckGo / Bing — engines defined entirely by engines/*.json, no MFL
./fetchers/duckduckgo.sh "machin programming language" | ./open-serpapi parse --engine duckduckgo
./fetchers/bing.sh       "machin programming language" | ./open-serpapi parse --engine bing
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
src/css.src         # HTML -> DOM + CSS-selector engine + spec runner
engines/<name>.json # declarative spec-driven engines (e.g. duckduckgo) + how-to
build.sh            # encode src/*.src -> .mfl -> native binary
fetchers/           # layer-1 plugins (the pipe boundary) + the contract
fixtures/<engine>/  # frozen raw fetcher output (parser input)
golden/<engine>/    # expected output (parser spec)
test.sh             # run fixtures through the parser, diff goldens
```

## License

MIT.
