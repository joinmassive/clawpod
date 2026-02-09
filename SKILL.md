---
name: clawpod
description: Fetch web pages through residential proxy IPs with geo-targeting by country, city, state, or zipcode. Powered by the Massive proxy network. Use when the agent needs to access geo-restricted content, avoid IP bans, or fetch pages from specific locations.
command-dispatch: tool
command-tool: clawpod
metadata: {"version": "0.1.0", "tags": ["proxy", "residential-proxy", "geo-targeting", "web-fetch", "scraping"], "openclaw": {"requires": {"bins": ["python3"], "env": ["MASSIVE_PROXY_USERNAME", "MASSIVE_PROXY_PASSWORD"]}, "primaryEnv": "MASSIVE_PROXY_USERNAME"}}
---

# ClawPod

Fetch URLs through residential proxy IPs via the Massive network. Not a search engine — you give it a URL, it fetches it through a real residential IP with optional geo-targeting.

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

**Combine flags for precision:**

| Targeting need | Flags |
|----------------|-------|
| Any IP in Germany | `--country DE` |
| IP in New York City | `--country US --city "New York" --state NY` |
| IP in a specific US zipcode | `--country US --zipcode 90210` |
| IP in London | `--country GB --city London` |
| No geo preference (any residential IP) | *(omit all geo flags)* |

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
  "body": "{\n  \"origin\": \"73.162.45.89\"\n}"
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

---

## Important Notes

- This tool fetches **ONE URL at a time**. For multiple URLs, call it multiple times.
- Always check if a URL is accessible without a proxy first. Only use clawpod if you need geo-targeting or the site blocks non-residential IPs.
- The body is already included in the output. Do NOT use web_fetch or other tools to re-fetch the same URL.
- Each invocation uses a different residential IP. Re-run to get a new IP.
- This tool does **NOT** follow HTTP redirects (301, 302, 307, 308). If you receive a 3xx status, check the `Location` header and re-invoke with the new URL.
- No external dependencies — uses Python standard library only.
