# Skills

Self-contained, agent-loadable guides for using open-serpapi. Each is a single
`.md` an agent can read in one call.

- **[open-serpapi.md](open-serpapi.md)** — start here. The fetch→parse→schema model,
  building the binary, every engine + output schema, fetchers, adding a declarative
  engine, and testing. Covers the web engines (`google`, `duckduckgo`, `bing`,
  `startpage`, `brave`) and `google_maps`.
- **[linkedin.md](linkedin.md)** — the authed `linkedin` engine: keyword **post**
  search + per-post **comment** extraction, the CDP browser-attach fetcher and
  `grab` mode, the exact capability map (posts-by-keyword ✅ / comments per-post ✅ /
  keyword→comments-in-one-step ⚠️), and the ToS/account caveat.

These also live next to the code so the repo is self-documenting for any agent that
clones it.
