# ClawPod

Fetch web pages through residential proxy IPs via the Massive network. Geo-target by country, city, state, or zipcode. Sticky sessions, device-type targeting, and exit node metadata. Single Python script, zero external dependencies — uses only the Python standard library.

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

Sign up at [Massive](https://partners.joinmassive.com/create-account-clawpod) and purchase a residential proxy plan. Get your proxy credentials from the dashboard and add them to `~/.openclaw/.env` or `~/.openclaw/skills/clawpod/.env`:

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
| `--session` | No | Sticky session ID (up to 255 chars) |
| `--session-ttl` | No | Session TTL in minutes (1-240, default: 15) |
| `--session-mode` | No | `strict` (default) or `flex` |
| `--type` | No | Device type: `mobile`, `common`, or `tv` |

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

# Sticky session — reuse the same exit IP across requests
python3 scripts/fetch.py -u "https://httpbin.org/ip" --session mysession1

# Sticky session with custom TTL and flex error mode
python3 scripts/fetch.py -u "https://httpbin.org/ip" --session mysession1 --session-ttl 30 --session-mode flex

# Fetch through a mobile device IP
python3 scripts/fetch.py -u "https://example.com" --type mobile --country US
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
  "body": "{\n  \"origin\": \"73.162.45.89\"\n}",
  "exit_node": {
    "ip": "73.162.45.89",
    "country": "US",
    "timezone": "America/New_York",
    "asn": "7922"
  }
}
```

The `exit_node` field is included for HTTPS requests and contains metadata about the proxy exit node (IP, country, timezone, ASN). Use it to verify geo-targeting.

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

**Notes:**
- `--country` is required when using any other geo flag
- Geotargeting by country + city is more robust than by zipcode
- If both `--state` and `--zipcode` are specified, `--city` is ignored
- Overly narrow constraints may return a 503 — relax parameters if needed

---

## Sticky Sessions

Use sticky sessions to route multiple requests through the **same exit IP**. Useful for multi-page scraping or sites that track IP consistency.

| Flag | Description | Default |
|------|-------------|---------|
| `--session` | Session ID (up to 255 chars) | *(none)* |
| `--session-ttl` | TTL in minutes (1-240) | 15 |
| `--session-mode` | `strict` or `flex` | `strict` |

- **strict** (default): any proxy error invalidates the session and rotates to a new IP
- **flex**: tolerates transient errors — session persists until too many consecutive failures
- TTL is static — expires at creation time + TTL, not extended by subsequent requests
- Changing `--country` or `--city` creates a different session

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

## FAQ & Troubleshooting

**Q: Do I need to install any Python packages?**
> No. ClawPod uses only the Python standard library. No pip install required.

**Q: What Python version do I need?**
> Python 3.8 or later.

**Q: How do I get a new IP?**
> Each invocation uses a different residential IP automatically, unless you use `--session`. Just re-run the command.

**Q: How do I keep the same IP across requests?**
> Use `--session myid` with the same session ID. The IP stays the same for 15 minutes by default (adjust with `--session-ttl`).

**Error: "Missing Massive proxy credentials"**
```bash
# Add to ~/.openclaw/.env or ~/.openclaw/skills/clawpod/.env
echo 'MASSIVE_PROXY_USERNAME="your-username"' >> ~/.openclaw/.env
echo 'MASSIVE_PROXY_PASSWORD="your-password"' >> ~/.openclaw/.env
```

**Error: "Proxy authentication failed (407)"**
> Your credentials are invalid. Check MASSIVE_PROXY_USERNAME and MASSIVE_PROXY_PASSWORD in your .env file. Verify them at [partners.joinmassive.com](https://partners.joinmassive.com/login).

**Error: "Connection timed out"**
> The proxy or target server didn't respond within the timeout. Retry the request.

**Error: "SSL error"**
> The target server has SSL issues. This is usually a problem with the target site, not the proxy.

**Error: "Disallowed content (452)"**
> The protocol, port, or content conflicts with Massive's content policy. Only ports 80/443 are allowed.

**Error: "Service unavailable (503)"**
> Geo-targeting constraints could not be met. Try relaxing location parameters (e.g. drop `--city` or `--zipcode`).

**Error: "No upstream proxy available (521)"**
> Insufficient proxy capacity for the specified location or ASN. Try a broader region.

---

## Links

- [Massive](https://joinmassive.com) — Residential proxy network
- [Massive Portal](https://partners.joinmassive.com/create-account-clawpod) — Sign up and manage credentials
