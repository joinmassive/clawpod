---
name: clawpod
description: Fetch any web page via Massive's Unblocker REST API. Handles JavaScript rendering, anti-bot protection, CAPTCHAs, paywalls, and geo-restrictions server-side — returns clean extracted markdown. Use for any web fetching, scraping, or content extraction task where standard HTTP requests would be blocked.
allowed-tools: Bash(curl:*), Bash(node:*), Bash(npm:*)
homepage: https://clawpod.joinmassive.com
metadata: {"openclaw":{"emoji":"🔓","homepage":"https://clawpod.joinmassive.com","primaryEnv":"MASSIVE_UNBLOCKER_TOKEN","requires":{"bins":["curl"],"env":["MASSIVE_UNBLOCKER_TOKEN"]}}}
---

# Massive Unblocker

Fetch and extract content from URLs using Massive's Unblocker Browser API. Handles JS rendering, CAPTCHAs, and retries automatically. Returns clean markdown with headings, links, lists, tables, and code blocks.

## Setup

Check for the API token and try to set up node-html-markdown:

```bash
echo "TOKEN=${MASSIVE_UNBLOCKER_TOKEN:-MISSING}"
node -e "require('node-html-markdown')" 2>/dev/null || npm install -g node-html-markdown 2>/dev/null || echo "NHM=UNAVAILABLE (will fall back to raw HTML)"
```

If token is `MISSING`, stop and tell the user:

1. Go to **clawpod.joinmassive.com/waitlist** to get an API token.
2. Ask them to provide it.
3. Store it so the environment can access it (e.g., export or settings file).
4. Do not proceed until the token is available.

If node-html-markdown is unavailable, proceed anyway — raw HTML will be returned and the LLM can parse it directly.

## How It Works

Single endpoint. `GET` request. Returns rendered HTML. Pipe through `node-html-markdown` for clean markdown (falls back to raw HTML if unavailable).

```
https://unblocker.joinmassive.com/browser?url=<encoded-url>
```

Auth header: `Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN`

## Fetching a URL

```bash
curl -s -G --data-urlencode "url=THE_URL" \
  -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/browser" -o /tmp/_page.html && \
  (node -e "const{NodeHtmlMarkdown}=require('node-html-markdown');console.log(NodeHtmlMarkdown.translate(require('fs').readFileSync('/tmp/_page.html','utf8')))" 2>/dev/null || cat /tmp/_page.html)
```

Replace `THE_URL` with the actual URL. `curl --data-urlencode` handles URL-encoding automatically.

## Fetching Multiple URLs

Loop through them sequentially. Each call can take up to 2 minutes (CAPTCHA solving, retries).

```bash
URLS=(
  "https://example.com/page1"
  "https://example.com/page2"
)

for url in "${URLS[@]}"; do
  echo "=== $url ==="
  curl -s -G --data-urlencode "url=$url" \
    -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
    "https://unblocker.joinmassive.com/browser" -o /tmp/_page.html && \
    (node -e "const{NodeHtmlMarkdown}=require('node-html-markdown');console.log(NodeHtmlMarkdown.translate(require('fs').readFileSync('/tmp/_page.html','utf8')))" 2>/dev/null || cat /tmp/_page.html)
done
```

## Optional Parameters

Append to the query string as needed:

| Parameter | Values | Default | Use when |
|-----------|--------|---------|----------|
| `format` | `rendered`, `raw` | `rendered` | Use `raw` to skip JS rendering (faster) |
| `expiration` | `0` to N (days) | `1` | Set `0` to bypass cache |
| `delay` | `0.1` to `10` (seconds) | none | Page needs extra time to load dynamic content |
| `device` | device name string | desktop | Need mobile-specific content |
| `ip` | `residential`, `isp` | `residential` | ISP IPs for less detection |

Example with options:

```bash
curl -s -G --data-urlencode "url=THE_URL" \
  -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/browser?expiration=0&delay=2" -o /tmp/_page.html && \
  (node -e "const{NodeHtmlMarkdown}=require('node-html-markdown');console.log(NodeHtmlMarkdown.translate(require('fs').readFileSync('/tmp/_page.html','utf8')))" 2>/dev/null || cat /tmp/_page.html)
```

## Rules

- **One fetch = one result.** The markdown content is in the output. Do not re-fetch the same URL.
- **URL-encode the target URL.** Always.
- **Sequential for multiple URLs.** No parallel requests.
- **2 minute timeout per request.** If a page is slow, it's the API handling retries/CAPTCHAs.
- **Pipe through node-html-markdown when available.** It converts HTML to clean markdown. If unavailable, raw HTML is returned — the LLM can still parse it.
