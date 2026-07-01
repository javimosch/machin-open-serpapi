# Fetchers — the plugin boundary (layer 1)

open-serpapi does **not** fetch. It parses. A *fetcher* is any program that takes a
query and writes **raw bytes** to stdout; open-serpapi reads those bytes on stdin and
emits structured JSON:

```
<fetcher> "query"  |  ./open-serpapi parse --engine <engine>
```

That's the whole contract:

| | |
|---|---|
| **input** | `argv[1]` = the query (plus any engine-specific flags you define) |
| **output** | raw bytes on stdout — whatever your scraper produces for that engine |
| **language** | anything: bash+curl, a headless/anti-detect browser, a paid API, `cat fixture.html` |
| **network/TLS** | lives entirely here, never in open-serpapi |

Because the binary never touches the network, it has **no TLS dependency**, is
**deterministic**, and is **offline-testable** against the saved fixtures in
[`../fixtures/`](../fixtures) — no fetcher required for `./test.sh`.

## What each engine expects on stdin

- **`google`** → rendered Google SERP HTML → `organic_results[]`.
- **`google_maps`** → a raw record array (JSON) `{name, rating, reviews_count, address,
  website, phone, type, query, lat, lng, place_id, maps_url}` → `local_results[]`.
- **`duckduckgo` / `bing` / `startpage` / `brave`** → that engine's SERP HTML →
  `organic_results[]` (declarative CSS specs in [`../engines/`](../engines)).
- **`linkedin`** → authed LinkedIn HTML → `posts[]` with nested `comments[]`.

## Bring your own

Write a fetcher in any language — the only requirement is *query in, raw page out*.
Reference fetcher implementations (anti-detect browser renderers, an authed LinkedIn
harvester, etc.) are maintained **separately** so open-serpapi stays a clean,
network-free parse+schema core. For CI and reproducible parsing, use the frozen
fixtures rather than a live fetcher.
