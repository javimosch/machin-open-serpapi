---
name: open-serpapi-linkedin
description: Use the open-serpapi `linkedin` engine to extract LinkedIn posts (by keyword) and a post's comments as JSON, from your own logged-in session. Covers the CDP browser-attach fetcher, the li_at fallback, keyword post search, per-post comment extraction, what is and isn't possible (posts-by-keyword vs comments), and the ToS/account risk. Read open-serpapi.md first.
---

# open-serpapi: LinkedIn

The `linkedin` engine parses **logged-in** LinkedIn HTML into `posts[]`, each with
nested `comments[]`. It auto-detects two page shapes:

- **content-search** (obfuscated class names) → posts. Anchors on the stable
  `data-testid="expandable-text-box"`; author name from the control-menu
  aria-label (EN/ES/FR), profile from the nearest `/in/`|`/company/` link.
- **post-detail** (classic semantic classes) → the post **+ its comments**.
  Each comment via `comments-comment-meta__description-title` (author) paired with
  `comments-comment-item__main-content` (text) in document order.

## Capability map — what you CAN and CANNOT do today

| goal | supported? | how |
|---|---|---|
| **Search posts by keyword** | ✅ yes | `linkedin.sh content "<keywords>"` → `posts[]` (author, author_url, author_type, text, hashtags). Language-independent. |
| Posts by author/company | ✅ yes | `linkedin.sh url "https://www.linkedin.com/in/<slug>/recent-activity/all/"` |
| **Comments of a specific post** | ✅ yes | `linkedin.sh url "https://www.linkedin.com/feed/update/urn:li:activity:<id>/"` → `posts[0].comments[]` |
| **Comments for keyword-matched posts (one step)** | ⚠️ **no** | The content-search DOM does **not** expose per-post permalinks/URNs, so there is no automatic keyword → posts → comments chain. Do it in two manual steps: search for posts, then fetch each post's detail URL (when you have it) or use `grab`. |
| Reaction counts / reactor list | ❌ not yet | not parsed |

So: **posts-by-keyword = yes; comments = yes but per-post**, not auto-joined to a
keyword search. To go from a keyword to comments you currently need the post's URL
(open it in the browser and `grab`, or paste a `/feed/update/<urn>/` URL).

## Fetching (authed) — prefer CDP attach to your real browser

li_at-cookie injection works for content-search but the comment-bearing pages hit
anti-bot (HTTP 429 / `ERR_TOO_MANY_REDIRECTS` / PerimeterX). Driving your **real,
already-authenticated browser** over the DevTools Protocol avoids all of it.

```bash
# 1. launch your browser with a debug port (keeps your profile/session + tabs):
DISPLAY=:0 setsid microsoft-edge --remote-debugging-port=9222 \
  --profile-directory=Default --restore-last-session >/dev/null 2>&1 &
#    (DISPLAY + setsid are required, else the GUI process dies.)

# 2. fetch — linkedin.sh auto-detects localhost:9222 and uses it:
./fetchers/linkedin.sh content "staff augmentation Grenoble" | ./open-serpapi parse --engine linkedin
./fetchers/linkedin.sh url "https://www.linkedin.com/feed/update/urn:li:activity:<id>/" | ./open-serpapi parse --engine linkedin

# 3. grab: capture a post you've ALREADY opened + scrolled (comments loaded) — the
#    most reliable way to get a full comment thread (no lazy-load fighting):
./fetchers/linkedin.sh grab | ./open-serpapi parse --engine linkedin
```

Fallback (no debug port): set a `li_at` cookie in `~/.config/intrane-gtm/li_at`
(chmod 600) or `$LI_AT`. Good for content-search; comment pages may be blocked.

## Output schema

```json
{
  "search_metadata":   { "status": "Success", "engine": "linkedin" },
  "search_parameters": { "engine": "linkedin", "q": "..." },
  "posts": [
    { "position": 1, "author": "Jane Doe",
      "author_url": "https://www.linkedin.com/in/jane-doe-123/",
      "author_type": "person", "text": "...", "hashtags": ["DevOps"],
      "comment_count": 2,
      "comments": [
        { "author": "Alex Smith",
          "author_url": "https://www.linkedin.com/in/alex-smith-9/",
          "author_type": "person", "headline": "Platform Engineer",
          "text": "..." }
      ] }
  ]
}
```

On a content-search page `comments` is `[]` (search lists posts only); on a
post-detail/grab page `posts[0]` is the post with its `comments[]` filled.

## GTM use (intrane.fr) — the agent loop

Posts give **what topics/hashtags are active and who's posting**; a post's comments
give **who's engaging and their headlines/roles** — directly actionable for "who to
reach and where to post". Typical flow an external agent runs:
1. `linkedin.sh content "<ICP topic>"` → posts + hashtags → topic/author signal.
2. Open a high-engagement post in the browser, scroll, `linkedin.sh grab` → its
   commenters (names, profiles, headlines) → warm leads / people to engage.

## ⚠️ ToS / account risk

Scraping logged-in LinkedIn violates their User Agreement and **can get your account
restricted**. Keep it **personal and low-volume** (LinkedIn rate-limits hard). The
`li_at` token is a full session secret — read only from `$LI_AT` /
`~/.config/intrane-gtm/li_at`, never printed or committed. **Never commit rendered
authed HTML** (it carries your session + real people's data) — repo fixtures are
synthetic.
