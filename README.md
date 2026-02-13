# ClawPod

Fetch and extract web page content through Massive's Unblocker REST API. Handles JavaScript rendering, anti-bot protection, CAPTCHAs, paywalls, and geo-restrictions server-side — returns rendered HTML that can be converted to clean markdown.

---

## How It Works

1. **You provide a URL** — the target page to fetch
2. **Unblocker handles the rest** — JS rendering, CAPTCHA solving, retries, and anti-bot bypass all happen server-side
3. **Content returned** — rendered HTML, optionally converted to markdown via `node-html-markdown`

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

---

## API Parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `url` | any URL | *(required)* | Target page to fetch |
| `format` | `rendered`, `raw` | `rendered` | `raw` skips JS rendering (faster) |
| `expiration` | `0` to N (days) | `1` | `0` bypasses cache |
| `delay` | `0.1` to `10` (seconds) | none | Extra wait for dynamic content |
| `device` | device name string | desktop | Device type for content |
| `ip` | `residential`, `isp` | `residential` | ISP IPs for less detection |

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
