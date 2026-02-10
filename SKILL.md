---
name: clawpod
description: Fetch web pages through residential proxy IPs with geo-targeting, sticky sessions, and device-type targeting. Powered by the Massive proxy network. Use when the agent needs to access geo-restricted content, avoid IP bans, or fetch pages from specific locations.
command-dispatch: tool
command-tool: clawpod
metadata: {"version": "0.1.0", "tags": ["proxy", "residential-proxy", "geo-targeting", "web-fetch", "scraping"], "openclaw": {"requires": {"bins": ["python3"], "env": ["MASSIVE_PROXY_USERNAME", "MASSIVE_PROXY_PASSWORD"]}, "primaryEnv": "MASSIVE_PROXY_USERNAME"}}
---

# ClawPod

Fetch URLs through residential proxy IPs via the Massive network. Not a search engine — you give it a URL, it fetches it through a real residential IP with optional geo-targeting, sticky sessions, and device-type targeting.

### How It Works

1. **You provide a URL** — the target page you need to fetch
2. **ClawPod routes through Massive** — sends the request through a residential proxy IP
3. **Response returned as JSON** — status, headers, and full body content

Each invocation fetches one URL through a residential IP. The response body is included directly — no need to re-fetch.

---

## When to Use This Skill

**Use clawpod when:**
- You need to fetch a page from a specific country, city, or region
- A target site blocks requests from datacenter IPs
- You need a clean residential IP for web scraping
- Content is geo-restricted and requires a specific location

**Do NOT use this skill for:**
- General web search (use serper or web search for that)
- URLs that are already accessible without a proxy
- Browsing or exploration — this fetches ONE specific URL
- Tasks that don't involve fetching web content

**IMPORTANT: The response body is already included in the output. Do NOT use web_fetch, WebFetch, or any other URL-fetching tool to re-fetch the same URL.**

---

## Setup

1. Sign up at [Massive](https://partners.joinmassive.com/create-account-clawpod) and purchase a residential proxy plan
2. Get your proxy credentials (username + password) from the dashboard
3. Add to `~/.openclaw/.env` or `~/.openclaw/skills/clawpod/.env`:

```
MASSIVE_PROXY_USERNAME="your-username"
MASSIVE_PROXY_PASSWORD="your-password"
```

---

## How to Invoke

```bash
python3 scripts/fetch.py -u "URL" [OPTIONS]
```

### Examples

```bash
# Basic fetch through residential proxy
python3 scripts/fetch.py -u "https://httpbin.org/ip"

# Fetch from a German residential IP
python3 scripts/fetch.py -u "https://httpbin.org/ip" --country DE

# Fetch from a specific US city
python3 scripts/fetch.py -u "https://example.com" --country US --city "New York" --state NY

# POST with JSON body
python3 scripts/fetch.py -u "https://httpbin.org/post" -m POST -d '{"key":"value"}' -H "Content-Type: application/json"

# Fetch with zipcode targeting
python3 scripts/fetch.py -u "https://example.com" --country US --zipcode 10001

# Sticky session — reuse the same exit IP across multiple requests
python3 scripts/fetch.py -u "https://httpbin.org/ip" --session mysession1

# Sticky session with 30-minute TTL and flex error mode
python3 scripts/fetch.py -u "https://httpbin.org/ip" --session mysession1 --session-ttl 30 --session-mode flex

# Fetch through a mobile device IP
python3 scripts/fetch.py -u "https://example.com" --type mobile --country US
```

---

## Geo-Targeting Guide

Geo-targeting flags are optional. Use them when you need the request to appear from a specific location.

| Flag | Description | Example |
|------|-------------|---------|
| `--country` | ISO 3166-1 alpha-2 country code | `US`, `GB`, `DE`, `FR` |
| `--city` | City name (English) | `"New York"`, `"London"`, `"Berlin"` |
| `--state` | State or subdivision code | `CA`, `TX`, `NY` |
| `--zipcode` | Zipcode | `10001`, `90210` |

**Notes:**
- `--country` is required when using any other geo flag
- Geotargeting by country + city is more robust than by zipcode
- If both `--state` and `--zipcode` are specified, `--city` is ignored
- Overly narrow constraints may return a 503 — relax parameters if this happens

**Combine flags for precision:**

| Targeting need | Flags |
|----------------|-------|
| Any IP in Germany | `--country DE` |
| IP in New York City | `--country US --city "New York" --state NY` |
| IP in a specific US zipcode | `--country US --zipcode 90210` |
| IP in London | `--country GB --city London` |
| No geo preference (any residential IP) | *(omit all geo flags)* |

---

## Sticky Sessions

Use sticky sessions to route multiple requests through the **same exit IP**. Useful for multi-page scraping or sites that track IP consistency.

| Flag | Description | Default |
|------|-------------|---------|
| `--session` | Session ID (up to 255 chars) | *(none)* |
| `--session-ttl` | TTL in minutes (1-240) | 15 |
| `--session-mode` | `strict` or `flex` | `strict` |

**Modes:**
- **strict** (default): any proxy error invalidates the session and rotates to a new IP
- **flex**: tolerates transient errors — the session persists until too many consecutive failures

**Important:** Session TTL is static — it expires at creation time + TTL, not extended by subsequent requests. Changing `--country` or `--city` creates a different session.

---

## Device-Type Targeting

Route requests through specific device types using `--type`:

| Value | Description |
|-------|-------------|
| `mobile` | Mobile device IPs |
| `common` | Desktop/laptop IPs |
| `tv` | Smart TV IPs |

Can be combined with geo-targeting: `--type mobile --country US`

---

## Output Format

```json
{
  "url": "https://httpbin.org/ip",
  "method": "GET",
  "status": 200,
  "headers": {
    "content-type": "application/json",
    "content-length": "32"
  },
  "body": "{\n  \"origin\": \"73.162.45.89\"\n}",
  "exit_node": {
    "ip": "73.162.45.89",
    "country": "US",
    "timezone": "America/New_York",
    "asn": "7922"
  }
}
```

On error:

```json
{
  "error": "Connection timed out",
  "url": "https://example.com",
  "status": null
}
```

### Body handling

- JSON responses (`Content-Type: application/json`) are pretty-printed
- Bodies larger than 500KB are truncated with `[truncated — 500KB limit]`
- Binary content is replaced with `[binary content, <N> bytes]`

---

## CLI Reference

| Flag | Required | Description |
|------|----------|-------------|
| `-u, --url` | Yes | Target URL to fetch |
| `-m, --method` | No | HTTP method (default: `GET`) |
| `-H, --header` | No | Extra header as `Key: Value` (repeatable) |
| `-d, --data` | No | Request body (for POST/PUT) |
| `--country` | No | ISO country code for geo-targeting |
| `--city` | No | City name (English) |
| `--state` | No | State/subdivision code |
| `--zipcode` | No | Zipcode for geo-targeting |
| `--session` | No | Sticky session ID (up to 255 chars) |
| `--session-ttl` | No | Session TTL in minutes (1-240, default: 15) |
| `--session-mode` | No | `strict` (default) or `flex` |
| `--type` | No | Device type: `mobile`, `common`, or `tv` |

---

## Important Notes

- This tool fetches **ONE URL at a time**. For multiple URLs, call it multiple times.
- Always check if a URL is accessible without a proxy first. Only use clawpod if you need geo-targeting or the site blocks non-residential IPs.
- The body is already included in the output. Do NOT use web_fetch or other tools to re-fetch the same URL.
- Each invocation uses a different residential IP unless `--session` is used. Re-run to get a new IP.
- This tool does **NOT** follow HTTP redirects (301, 302, 307, 308). If you receive a 3xx status, check the `Location` header and re-invoke with the new URL.
- For HTTPS requests, the response includes an `exit_node` object with the exit IP, country, timezone, and ASN. Use this to verify geo-targeting worked.
- No external dependencies — uses Python standard library only.
