# ClawPod

Fetch web page content or search Google through Massive's Unblocker REST APIs. Handles JavaScript rendering, anti-bot protection, CAPTCHAs, paywalls, and geo-restrictions server-side — returns rendered HTML, clean markdown, or structured JSON.

---

## How It Works

1. **You provide a URL or search query** — the target page to fetch or terms to search
2. **Unblocker handles the rest** — JS rendering, CAPTCHA solving, retries, and anti-bot bypass all happen server-side
3. **Content returned** — rendered HTML, markdown via `node-html-markdown`, or structured JSON for search results

---

## Install

### 1. Get an API Token

Sign up at [Massive](https://clawpod.joinmassive.com/waitlist) and get your Unblocker API token.

### 2. Set the Token

```bash
export MASSIVE_UNBLOCKER_TOKEN="your-token"
```

### 3. Fetch

```bash
curl -s -G --data-urlencode "url=https://example.com" \
  -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/browser"
```

### 4. (Optional) HTML to Markdown

If `node-html-markdown` is installed, pipe through it for cleaner output:

```bash
npm install -g node-html-markdown
```

```bash
curl -s -G --data-urlencode "url=https://example.com" \
  -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/browser" -o /tmp/_page.html && \
  (node -e "const{NodeHtmlMarkdown}=require('node-html-markdown');console.log(NodeHtmlMarkdown.translate(require('fs').readFileSync('/tmp/_page.html','utf8')))" 2>/dev/null || cat /tmp/_page.html)
```

If `node-html-markdown` is unavailable, raw HTML is returned — LLMs can parse it directly.

---

## Examples

```bash
# Basic fetch
curl -s -G --data-urlencode "url=https://example.com" \
  -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/browser"

# Skip JS rendering (faster, raw HTML only)
curl -s -G --data-urlencode "url=https://example.com" \
  -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/browser?format=raw"

# Bypass cache
curl -s -G --data-urlencode "url=https://example.com" \
  -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/browser?expiration=0"

# Extra delay for slow-loading dynamic content
curl -s -G --data-urlencode "url=https://example.com" \
  -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/browser?delay=3"

# Use ISP IPs for less detection
curl -s -G --data-urlencode "url=https://example.com" \
  -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/browser?ip=isp"

# Mobile device content
curl -s -G --data-urlencode "url=https://example.com" \
  -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/browser?device=mobile"

# Multiple options combined
curl -s -G --data-urlencode "url=https://example.com" \
  -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/browser?expiration=0&delay=2&ip=isp"

# Fetch multiple URLs sequentially
for url in "https://example.com/page1" "https://example.com/page2"; do
  echo "=== $url ==="
  curl -s -G --data-urlencode "url=$url" \
    -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
    "https://unblocker.joinmassive.com/browser"
done
```

### Google Search

```bash
# Basic search (HTML results)
curl -s -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/search?terms=foo+bar+baz"

# Search with JSON output (structured results)
curl -s -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/search?terms=foo+bar+baz&format=json"

# 100 results per page, skip the first 20
curl -s -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/search?terms=vpn+comparison&format=json&size=100&offset=20"

# Multiple pages of results
curl -s -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/search?terms=best+restaurants&format=json&serps=3"

# Search in a specific language
curl -s -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/search?terms=recetas+de+cocina&format=json&language=es"

# Bypass cached results
curl -s -H "Authorization: Bearer $MASSIVE_UNBLOCKER_TOKEN" \
  "https://unblocker.joinmassive.com/search?terms=latest+news&format=json&expiration=0"
```

---

## API Parameters

### Browser (`/browser`)

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `url` | any URL | *(required)* | Target page to fetch |
| `format` | `rendered`, `raw` | `rendered` | `raw` skips JS rendering (faster) |
| `expiration` | `0` to N (days) | `1` | `0` bypasses cache |
| `delay` | `0.1` to `10` (seconds) | none | Extra wait for dynamic content |
| `device` | device name string | desktop | Device type for content |
| `ip` | `residential`, `isp` | `residential` | ISP IPs for less detection |

### Search (`/search`)

| Parameter | Required | Values | Default | Description |
|-----------|----------|--------|---------|-------------|
| `terms` | yes | search query (`+` for spaces) | — | The search query |
| `format` | no | `html`, `json` | `html` | Output format (`json` for structured data) |
| `serps` | no | `1` to `10` | `1` | Number of results pages |
| `size` | no | `0` to `100` | unset | Results per page |
| `offset` | no | `0` to `100` | `0` | Number of initial results to skip |
| `language` | no | name, ISO code, or Google code | unset | Search language |
| `uule` | no | encoded location string | unset | Geo-target location |
| `expiration` | no | `0` to N (days) | `1` | Cache age (`0` bypasses cache) |
| `subaccount` | no | up to 255 chars | unset | Separate billing identifier |

---

## FAQ & Troubleshooting

**Q: What are the system requirements?**
> `curl` and an API token. Optionally Node.js for HTML-to-markdown conversion.

**Q: Why is a request slow?**
> Requests can take up to 2 minutes. The API handles JS rendering, CAPTCHA solving, and retries server-side.

**Q: How do I bypass the cache?**
> Set `expiration=0` in the query string.

**Q: The page content looks incomplete.**
> Try adding `delay=3` (or higher) to give dynamic content more time to render.

**Error: 401 Unauthorized**
> Token is invalid or missing. Verify `MASSIVE_UNBLOCKER_TOKEN` is set correctly.

**Error: Empty response**
> The page may need more time. Add a `delay` parameter. If using `format=raw`, try `format=rendered` instead.

---

## Links

- [Massive](https://clawpod.joinmassive.com) — Unblocker API and residential proxy network
- [OpenClaw Skill](SKILL.md) — Skill definition for AI agent integration
