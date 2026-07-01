---
name: open-serpapi
description: Use open-serpapi to turn raw search-engine HTML into clean JSON from the CLI. Covers the fetch→parse→schema model, building the binary, every engine (google, google_maps, duckduckgo, bing, startpage, brave, linkedin), output schemas, fetchers, adding a new engine, and testing. Read this first. (LinkedIn fetching + the authed harvester live in a separate repo.)
---

# open-serpapi

A single native binary (written in machin/MFL) that parses rendered search pages
into structured JSON. **It never fetches** — fetching is a plugin. The pipe:

```
<fetcher> "query"  |  ./open-serpapi parse --engine <engine> [--query "q"]  ->  JSON
```

SerpApi sells three layers: **fetch** (get past blocking), **parse** (messy HTML →
structure), **schema** (a stable JSON shape). open-serpapi owns **parse + schema**
and makes fetch a swappable plugin, so it has no TLS/network dependency and is
deterministic + offline-testable.

## Build

```bash
./build.sh                              # encode src/*.src → build/*.mfl → ./open-serpapi
MACHIN=~/ai/machin/machin ./build.sh    # against a local machin compiler
```

## Invoke

```bash
# parse saved bytes (offline, no fetcher) — deterministic:
./open-serpapi parse --engine google      < fixtures/google/machin-lang.raw.html
./open-serpapi parse --engine duckduckgo  < fixtures/duckduckgo/machin-lang.raw.html

# end-to-end: pipe any fetcher (a script that prints a page to stdout) into parse:
<fetcher> "machin language" | ./open-serpapi parse --engine duckduckgo
```

`--query "q"` sets `search_parameters.q` (some engines also recover it from the page).

## Engines

| engine | input (stdin) | output key | per-item fields |
|---|---|---|---|
| `google` | rendered Google SERP HTML | `organic_results` | position, title, link, displayed_link, snippet |
| `duckduckgo` | DDG html-endpoint markup | `organic_results` | "" |
| `bing` | Bing SERP HTML | `organic_results` | "" (decodes `ck/a` redirect links) |
| `startpage` | Startpage SERP HTML | `organic_results` | "" |
| `brave` | Brave SERP HTML | `organic_results` | "" |
| `google_maps` | raw record array (JSON) | `local_results` | title, rating, reviews, type, address, phone, website, gps_coordinates, place_id, maps_url |
| `linkedin` | **authed** LinkedIn HTML | `posts` | author, author_url, author_type, text, hashtags, comments[] — authed; fetch via a separate repo |

`google` and `linkedin` are bespoke MFL parsers (irregular/obfuscated markup).
`duckduckgo`/`bing`/`startpage`/`brave` are **declarative**: a JSON selector spec
in `engines/<name>.json` run by the CSS-selector engine (`src/css.src`).

## Output shape (organic engines)

```json
{
  "search_metadata":   { "status": "Success", "engine": "brave" },
  "search_parameters": { "engine": "brave", "q": "machin language" },
  "organic_results": [
    { "position": 1, "title": "...", "link": "https://...",
      "displayed_link": "example.com › ...", "snippet": "..." }
  ]
}
```

## Fetchers (layer 1 — the plugin boundary)

Any program that prints a page to stdout is a fetcher — see the contract in
[`fetchers/README.md`](../fetchers/README.md). open-serpapi ships **no** fetchers;
they're maintained separately so the binary stays network-free. Typical shapes:

- anti-detect browser renderers (Botasaurus/Playwright) for `google/duckduckgo/bing/
  startpage/brave` — get past CAPTCHA/"unusual traffic" walls.
- a Google Maps scraper for `google_maps` (emits name/rating/reviews/address/phone/
  website/place_id/lat/lng/maps_url).
- an authed browser (CDP-attach to your own session) for `linkedin` — ToS-sensitive.

For CI/tests, use the saved fixtures (no network).

## Add a new engine (no MFL)

If the target has stable class names, it's just a JSON file — see `engines/README.md`:

```json
{ "engine": "mojeek", "output": "organic_results", "result": "ul.results-standard li",
  "fields": [ { "name":"title","sel":"a.title","get":"text" },
              { "name":"link","sel":"a.title","get":"@href" },
              { "name":"snippet","sel":"p.s","get":"text" } ] }
```

Supported selectors: tag, `.class`, `#id`, `[attr]`, `[attr="val"]`, compound
(`a.b.c`), descendant (space) and child (`>`). `get`: `text` or `@attr`.
`transform`: `url` (Google `/url?q=`), `ddg_redirect`, `bing_redirect`, `https`.
A result whose first field is empty is skipped (drops non-result blocks).

## Testing

```bash
./test.sh    # every fixtures/<engine>/<name>.raw.* parsed and diffed vs golden/<engine>/<name>.json
```

Add a case: drop a raw fixture, generate its golden
(`./open-serpapi parse --engine E < raw | jq . > golden/E/name.json`), eyeball, commit both.
Fixtures are **frozen real-page samples** (or synthetic where the source carries PII) —
deterministic and offline; live scrapers only run to refresh them when markup drifts.

## Caveats

- Google `snippet` is empty for `#:~:text=` highlight results (Google ships none).
- Search markup drifts; the corpus is the spec — refresh fixtures, don't chase live HTML.
- `linkedin` is authed and ToS-sensitive — the fetcher/harvester lives in a separate (private) repo.
