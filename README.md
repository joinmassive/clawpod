# ClawPod

Browse and fetch web pages through residential proxy IPs via the Massive network. Uses [agent-browser](https://github.com/vercel-labs/agent-browser) (Playwright/Chromium) for full JavaScript rendering, real browser fingerprints, screenshots, and page interaction — all routed through Massive residential proxies.

---

## How It Works

1. **You provide a URL** — the target page to browse or fetch
2. **ClawPod routes through Massive** — launches a headless Chromium browser through a residential proxy at `network.joinmassive.com:65535`
3. **Content extracted** — full page text, accessibility snapshots, screenshots, or HTML — after JavaScript has rendered

---

## Install

### 1. Install agent-browser

```bash
npm install -g agent-browser
agent-browser install          # downloads bundled Chromium
```

### 2. Credentials

Sign up at [Massive](https://partners.joinmassive.com/create-account-clawpod) and get your proxy credentials from the dashboard and set credentials as environment variables:

```bash
export MASSIVE_PROXY_USERNAME="your-username"
export MASSIVE_PROXY_PASSWORD="your-password"
```

### 3. Fetch

```bash
# Build proxy URL
PROXY_URL="https://${MASSIVE_PROXY_USERNAME}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"

# Open page through proxy, get text, close
agent-browser --proxy "$PROXY_URL" open "https://httpbin.org/ip"
agent-browser get text body
agent-browser close
```

---

## Examples

```bash
# Build proxy URL (no geo-targeting)
PROXY_URL="https://${MASSIVE_PROXY_USERNAME}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"

# Basic fetch through residential proxy
agent-browser --proxy "$PROXY_URL" open "https://httpbin.org/ip"
agent-browser get text body
agent-browser close

# Geo-targeted fetch from Germany
ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fcountry%3DDE"
PROXY_URL="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"
agent-browser --proxy "$PROXY_URL" open "https://httpbin.org/ip"
agent-browser get text body
agent-browser close

# Fetch from a specific US city
ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fcountry%3DUS%26city%3DNew%20York%26subdivision%3DNY"
PROXY_URL="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"
agent-browser --proxy "$PROXY_URL" open "https://example.com"
agent-browser get text body
agent-browser close

# Take a screenshot
PROXY_URL="https://${MASSIVE_PROXY_USERNAME}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"
agent-browser --proxy "$PROXY_URL" open "https://example.com"
agent-browser screenshot page.png
agent-browser close

# Accessibility snapshot (interactive elements)
agent-browser --proxy "$PROXY_URL" open "https://example.com"
agent-browser snapshot -i
agent-browser close

# Sticky session — reuse the same exit IP
ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fsession%3Dmysession1"
PROXY_URL="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"
agent-browser --proxy "$PROXY_URL" open "https://httpbin.org/ip"
agent-browser get text body
agent-browser open "https://httpbin.org/headers"   # same proxy, same IP
agent-browser get text body
agent-browser close

# Mobile device IP in the US
ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Ftype%3Dmobile%26country%3DUS"
PROXY_URL="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"
agent-browser --proxy "$PROXY_URL" open "https://example.com"
agent-browser get text body
agent-browser close
```

---

## Geo-Targeting

Geo-targeting parameters are encoded in the proxy username. See [SKILL.md](SKILL.md) for full details.

| Parameter | Description | Example values |
|-----------|-------------|----------------|
| `country` | ISO 3166-1 alpha-2 country code | `US`, `GB`, `DE`, `FR` |
| `city` | City name (English) | `New York`, `London`, `Berlin` |
| `subdivision` | State or subdivision code | `CA`, `TX`, `NY` |
| `zipcode` | Zipcode | `10001`, `90210` |

**Notes:**
- `country` is required when using any other geo parameter
- Country + city is more reliable than zipcode
- If both `subdivision` and `zipcode` are specified, `city` is ignored
- Overly narrow constraints may fail — relax parameters if needed

---

## Sticky Sessions

| Parameter | Description | Default |
|-----------|-------------|---------|
| `session` | Session ID (up to 255 chars) | *(none)* |
| `sessionttl` | TTL in minutes (1-240) | 15 |
| `sessionmode` | `strict` or `flex` | `strict` |

- **strict** (default): any proxy error invalidates the session and rotates to a new IP
- **flex**: tolerates transient errors — session persists until too many consecutive failures
- TTL is static — expires at creation time + TTL, not extended by subsequent requests

---

## Device-Type Targeting

| Value | Description |
|-------|-------------|
| `mobile` | Mobile device IPs |
| `common` | Desktop/laptop IPs |
| `tv` | Smart TV IPs |

---

## FAQ & Troubleshooting

**Q: What are the system requirements?**
> Node.js 18+ and a system that can run Chromium. On Linux, run `agent-browser install --with-deps` to install system dependencies.

**Q: How do I get a new IP?**
> Close and reopen the browser: `agent-browser close` then `agent-browser --proxy "$PROXY_URL" open <url>`. Each new daemon session gets a new IP unless you use sticky sessions.

**Q: How do I keep the same IP across requests?**
> Add a session parameter to the proxy username: `%3Fsession%3Dmyid`. All pages within the same daemon session use the same proxy.

**Q: Why is the first request slow?**
> The first `open` command launches Chromium (~3-8 seconds). Subsequent `open` commands within the same daemon session are faster.

**Error: "Missing Massive proxy credentials"**
> Set `MASSIVE_PROXY_USERNAME` and `MASSIVE_PROXY_PASSWORD` environment variables.

**Error: Proxy authentication failed**
> Credentials are invalid. Verify at [partners.joinmassive.com](https://partners.joinmassive.com/login).

**Error: Page content empty**
> The page may need more time to render. Try `agent-browser wait <seconds>` before extracting content.

---

## Links

- [agent-browser](https://github.com/vercel-labs/agent-browser) — Playwright/Chromium CLI for AI agents
- [Massive](https://joinmassive.com) — Residential proxy network
- [Massive Portal](https://partners.joinmassive.com/create-account-clawpod) — Sign up and manage credentials
