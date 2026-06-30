# Fetchers (layer 1 — the plugin boundary)

open-serpapi does **not** fetch. It parses. A *fetcher* is any program that
takes a query and writes **raw bytes** to stdout; open-serpapi reads those bytes
on stdin and emits SerpApi-shaped JSON.

```
<fetcher> "query"  |  open-serpapi parse --engine <engine>
```

That's the whole contract:

| | |
|---|---|
| **input** | `argv[1]` = the query (plus any engine-specific flags you define) |
| **output** | raw bytes on stdout — whatever your scraper produces for that engine |
| **language** | anything: bash+curl, Node/Puppeteer, Python, a Go binary, `cat fixture.html` |
| **network/TLS** | lives entirely here, never in open-serpapi |

A fetcher can be a real scraper, an official search API (bring your own key), a
proxy-backed crawler, or a cached file. Swap fetchers without touching the parser.

## What each engine's parser expects on stdin

- **`google_maps`** → the raw record array a Maps scraper emits, objects shaped
  `{name, rating, reviews_count, address, website, phone, type, query}`.
  Missing fields become `null` in the output. See `../fixtures/google_maps/`.

## Included

- **`google-maps.sh`** — wraps the existing Puppeteer Maps scraper under `~/ai`
  as a live smoke-test fetcher. Override the path with `MAPS_SCRAPER=...`.
  Use saved fixtures (not this) for CI — they're deterministic and offline.
