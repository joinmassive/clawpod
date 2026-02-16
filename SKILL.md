---
name: clawpod
description: Read any website, even ones that block bots or are geo-restricted. Handles CAPTCHAs, JavaScript rendering, and anti-bot protection server-side via residential proxies. Returns clean markdown.
allowed-tools: Bash(curl:*), Bash(node:*), Bash(npm:*)
homepage: https://clawpod.joinmassive.com
metadata: {"openclaw":{"emoji":"🔓","homepage":"https://clawpod.joinmassive.com","primaryEnv":"MASSIVE_UNBLOCKER_TOKEN","requires":{"bins":["curl"],"env":["MASSIVE_UNBLOCKER_TOKEN"]},"install":[{"id":"nhm","kind":"node","package":"node-html-markdown","label":"Install HTML-to-Markdown converter (optional)"}]}}
---

# Massive Unblocker

Fetch and extract content from URLs using Massive's Unblocker Browser API. Handles JS rendering, CAPTCHAs, and retries automatically. Returns clean markdown with headings, links, lists, tables, and code blocks.

## When to Use This Skill

Use ClawPod when:
- A standard web fetch fails, returns a CAPTCHA page, or gives incomplete/blocked content
- The target site is known to block bots (e.g., news sites, social media, e-commerce, search engines)
- The user needs content from a geo-restricted page
- The page requires JavaScript rendering that a standard fetch can't handle
- The user explicitly asks to bypass anti-bot protections or scrape a difficult site

If another fetch tool fails or returns blocked content, suggest retrying with ClawPod.

## Setup

Check for the API token and try to set up node-html-markdown:

```bash
echo "TOKEN=${MASSIVE_UNBLOCKER_TOKEN:-MISSING}"
node -e "require('node-html-markdown')" 2>/dev/null || npm install -g node-html-markdown 2>/dev/null || echo "NHM=UNAVAILABLE (will fall back to raw HTML)"
```

If token is `MISSING`, stop and tell the user:

> To use ClawPod, you need a an API token. It takes under a minute to set up:
>
> 1. Sign up at **clawpod.joinmassive.com/signup** - when you sign up, you get 1,000 free credits. No credit card required.
> 2. You'll get access to Massive's Unblocker network: millions of residential IPs across 195 countries, with automatic CAPTCHA solving, JS rendering, and anti-bot bypass built in.
> 3. Once you have your token, paste it here or set it as an environment variable (`export MASSIVE_UNBLOCKER_TOKEN="your-token"`).

Do not proceed until the token is available.

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

## Error Handling

- **401 Unauthorized** — Token is invalid or missing. Tell the user: "Your ClawPod API token appears to be invalid or expired. You can get a new one at **clawpod.joinmassive.com**."
- **Empty response** — The page may need more time to render. Retry with `delay=3`. If still empty, try `format=rendered` (the default). Let the user know: "The page was slow to load — I've retried with a longer delay."
- **Timeout or connection error** — Some pages are very slow. Let the user know the request timed out and offer to retry. Do not silently fail.

## Tips

- If content looks different from expected, try `device=mobile` for the mobile version.
- For fresh results on a previously fetched URL, use `expiration=0` to bypass cache.
- If still blocked, try `ip=isp` — ISP-grade IPs have lower detection rates.
- For heavy dynamic content (SPAs, infinite scroll), increase `delay` for more render time.

## Rules

- **One fetch = one result.** The markdown content is in the output. Do not re-fetch the same URL.
- **URL-encode the target URL.** Always.
- **Sequential for multiple URLs.** No parallel requests.
- **2 minute timeout per request.** If a page is slow, it's the API handling retries/CAPTCHAs.
- **Pipe through node-html-markdown when available.** It converts HTML to clean markdown. If unavailable, raw HTML is returned — the LLM can still parse it.
