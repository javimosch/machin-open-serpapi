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

- **`google`** → rendered SERP **HTML**. The parser anchors on structure (each
  organic result is an `<h3>` wrapped by an external `<a href>`, with `<cite>`
  + a `VwiC3b` snippet block), so it tolerates Google's randomized class names.
  Emits `organic_results[]`. See `../fixtures/google/`.
- **`google_maps`** → the raw record array a Maps scraper emits, objects shaped
  `{name, rating, reviews_count, address, website, phone, type, query}`.
  Missing fields become `null` in the output. See `../fixtures/google_maps/`.

## Included

- **`google.sh`** → **`google-botasaurus.py`** — the **CAPTCHA-bypassing** fetcher
  for `engine=google`. Drives [Botasaurus](https://github.com/omkarcloud/botasaurus)'
  anti-detect, humanized Chrome, which gets past Google's "unusual traffic" wall.
  **Verified:** 12 organic results from a live SERP where curl and plain headless
  Chrome got only the CAPTCHA page.
  ```bash
  ./fetchers/google.sh "machin programming language" | ./open-serpapi parse --engine google
  ```
  Needs `pip install botasaurus` (already present via the supercli `botasaurus-cli`).
- **`google-search.js`** — plain Puppeteer fetcher. Kept as a reference: from a
  datacenter IP it gets **CAPTCHA-walled** (use it only where you have a clean
  residential IP / logged-in session).
- **`google-maps.sh`** — wraps the existing Puppeteer Maps scraper under `~/ai`.
  Override the path with `MAPS_SCRAPER=...`.

> **The layer-1 reality:** plain HTTP (curl, TLS-impersonation) and naive headless
> browsers hit Google's CAPTCHA wall — that's the anti-bot arms race. open-serpapi
> doesn't *fight* it in the parser; it makes fetch a plugin so you can drop in one
> that wins. Botasaurus is a strong default; residential proxies or a logged-in
> session also work. The **parser** is what this project owns, and it's tested
> offline against saved fixtures regardless of how you fetch.
