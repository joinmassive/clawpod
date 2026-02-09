# ClawPod

Fetch web pages through residential proxy IPs via the Massive network. Geo-target by country, city, state, or zipcode. Single Python script, zero external dependencies — uses only the Python standard library.

---

## How It Works

1. **You provide a URL** — the target page to fetch
2. **ClawPod routes through Massive** — sends the request through a residential proxy at `network.joinmassive.com:65535`
3. **Response returned as JSON** — status code, headers, and full body content

For HTTPS targets, ClawPod establishes a CONNECT tunnel through the proxy, then wraps the connection in SSL. For HTTP targets, it sends the request directly through the proxy.

---

## Install

### 1. Clone

```bash
git clone https://github.com/joinmassive/openclaw-clawpod.git ~/.openclaw/skills/clawpod
```

### 2. Credentials

Sign up at [Massive](https://app.joinmassive.com) and purchase a residential proxy plan. Get your proxy credentials from the dashboard and add them to `~/.openclaw/.env` or `~/.openclaw/skills/clawpod/.env`:

```bash
echo 'MASSIVE_PROXY_USERNAME="your-username"' >> ~/.openclaw/.env
echo 'MASSIVE_PROXY_PASSWORD="your-password"' >> ~/.openclaw/.env
```

### 3. Fetch

```bash
python3 ~/.openclaw/skills/clawpod/scripts/fetch.py -u "https://httpbin.org/ip"
```

No pip install needed — zero external dependencies.

---

## CLI Reference

| Flag | Required | Description |
|------|----------|-------------|
| `-u, --url` | Yes | Target URL to fetch |
| `-m, --method` | No | HTTP method (default: `GET`) |
| `-H, --header` | No | Extra header as `Key: Value` (repeatable) |
| `-d, --data` | No | Request body (for POST/PUT) |
| `--country` | No | ISO 3166-1 alpha-2 country code (e.g. `US`, `GB`, `DE`) |
| `--city` | No | City name for geo-targeting (English) |
| `--state` | No | State/subdivision code (e.g. `CA`, `TX`) |
| `--zipcode` | No | Zipcode for geo-targeting |

---

## Examples

```bash
# Basic fetch through residential proxy
python3 scripts/fetch.py -u "https://httpbin.org/ip"

# Geo-targeted fetch from Germany
python3 scripts/fetch.py -u "https://httpbin.org/ip" --country DE

# Fetch from a specific US city
python3 scripts/fetch.py -u "https://example.com" --country US --city "New York" --state NY

# POST with JSON body
python3 scripts/fetch.py -u "https://httpbin.org/post" -m POST -d '{"key":"value"}' -H "Content-Type: application/json"

# Fetch with zipcode targeting
python3 scripts/fetch.py -u "https://example.com" --country US --zipcode 10001
```

---

## Output Format

### Success

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

### Error

```json
{
  "error": "Connection timed out",
  "url": "https://example.com",
  "status": null
}
```

### Body Handling

- **JSON responses** (`Content-Type: application/json`) are pretty-printed
- **Large bodies** (>500KB) are truncated with `[truncated — 500KB limit]`
- **Binary content** (non-UTF-8) is replaced with `[binary content, <N> bytes]`

---

## Geo-Targeting

Geo-targeting flags are optional. They control which residential IP location to use.

| Targeting need | Flags |
|----------------|-------|
| Any IP in Germany | `--country DE` |
| IP in New York City | `--country US --city "New York" --state NY` |
| IP in a specific US zipcode | `--country US --zipcode 90210` |
| IP in London | `--country GB --city London` |
| No geo preference | *(omit all geo flags)* |

---

## FAQ & Troubleshooting

**Q: Do I need to install any Python packages?**
> No. ClawPod uses only the Python standard library. No pip install required.

**Q: What Python version do I need?**
> Python 3.8 or later.

**Q: How do I get a new IP?**
> Each invocation uses a different residential IP automatically. Just re-run the command.

**Error: "Missing Massive proxy credentials"**
```bash
# Add to ~/.openclaw/.env or ~/.openclaw/skills/clawpod/.env
echo 'MASSIVE_PROXY_USERNAME="your-username"' >> ~/.openclaw/.env
echo 'MASSIVE_PROXY_PASSWORD="your-password"' >> ~/.openclaw/.env
```

**Error: "Proxy authentication failed (407)"**
> Your credentials are invalid. Check MASSIVE_PROXY_USERNAME and MASSIVE_PROXY_PASSWORD in your .env file. Verify them at [app.joinmassive.com](https://app.joinmassive.com).

**Error: "Connection timed out"**
> The proxy or target server didn't respond within the timeout. Retry the request.

**Error: "SSL error"**
> The target server has SSL issues. This is usually a problem with the target site, not the proxy.

---

## Links

- [Massive](https://joinmassive.com) — Residential proxy network
- [Massive Portal](https://app.joinmassive.com) — Sign up and manage credentials
