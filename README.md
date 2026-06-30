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

Early scaffold. First engine: **`google_maps`** (raw record array → SerpApi
`local_results[]`). Roadmap: Google organic (an HTML tokenizer in MFL), a small
CSS-selector engine so engines become declarative, a server mode
(`GET /search?...` mapping `engine → fetcher`), and a SQLite result cache.

## Quick start

```bash
./build.sh                       # encode src/serpapi.src -> build, compile -> ./open-serpapi
MACHIN=~/ai/machin/machin ./build.sh   # against a local machin

# parse saved raw bytes (offline, no fetcher needed)
./open-serpapi parse --engine google_maps < fixtures/google_maps/coworking-annecy.raw.json

# end-to-end with a live fetcher plugin
./fetchers/google-maps.sh "coworking annecy" | ./open-serpapi parse --engine google_maps
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
src/serpapi.src     # the MFL core: parse + SerpApi schema (the whole product)
build.sh            # encode .src -> .mfl -> native binary
fetchers/           # layer-1 plugins (the pipe boundary) + the contract
fixtures/<engine>/  # frozen raw fetcher output (parser input)
golden/<engine>/    # expected SerpApi-shaped output (parser spec)
test.sh             # run fixtures through the parser, diff goldens
```

## License

MIT.
