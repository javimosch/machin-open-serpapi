# Declarative engines (CSS-selector specs)

A spec-driven engine is **just a JSON file** — no MFL, no recompile. Drop
`engines/<name>.json`, point a fetcher at the right URL, and run:

```bash
./fetchers/<name>.sh "query" | ./open-serpapi parse --engine <name>
# or with an explicit spec file:
... | ./open-serpapi parse --engine <name> --spec path/to/spec.json
```

open-serpapi parses the rendered HTML into a real DOM (`src/css.src`) and applies
the spec's selectors. This is how `duckduckgo` is defined — see
[`duckduckgo.json`](duckduckgo.json).

## Spec format

```json
{
  "engine": "duckduckgo",
  "output": "organic_results",
  "result": "div.web-result",
  "fields": [
    { "name": "title",          "sel": "a.result__a",       "get": "text" },
    { "name": "link",           "sel": "a.result__a",       "get": "@href", "transform": "ddg_redirect" },
    { "name": "displayed_link", "sel": "a.result__url",     "get": "text" },
    { "name": "snippet",        "sel": "a.result__snippet", "get": "text" }
  ]
}
```

| key | meaning |
|---|---|
| `engine` | name echoed into `search_metadata` / `search_parameters` |
| `output` | the JSON array key to emit (e.g. `organic_results`) |
| `result` | selector for each result container; one row per match |
| `fields[]` | per-row fields, each selected **scoped within** its container |
| `fields[].name` | output key |
| `fields[].sel` | CSS selector (first match wins) |
| `fields[].get` | `text` (inner text) or `@attr` (e.g. `@href`) |
| `fields[].transform` | optional: `ddg_redirect`, `url` (decode Google `/url?q=`), `https` (prefix `//…`) |

Each row also gets a 1-based `position`. A field whose selector matches nothing
becomes `""`.

## Supported CSS subset

Enough for real SERP markup, matched right-to-left over the DOM:

- type `div`, class `.result`, id `#main`, attribute `[href]`, `[data-x="y"]`
- compound: `a.result__a.foo`
- combinators: descendant (space) `div.result a`, child (`>`) `div.result > a`

Because the `result` selector scopes each container, non-organic blocks (ads,
"People also ask") are excluded structurally — e.g. DDG ads lack `web-result`.

## Adding an engine

1. Write `engines/<name>.json` against the target's stable classes.
2. Add `fetchers/<name>.sh` that emits the rendered HTML (reuse
   `render-botasaurus.py <url>` to get past bot walls).
3. Capture a fixture: `./fetchers/<name>.sh "q" > fixtures/<name>/<case>.raw.html`,
   then freeze a golden and add it to the offline suite (`./test.sh`).

Bespoke engines (`google`, `google_maps`) stay hand-written in MFL where the
markup is too irregular for selectors; spec-driven engines cover the clean ones.
