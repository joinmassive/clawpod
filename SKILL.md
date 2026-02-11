---
name: clawpod
description: Browse and fetch web pages through Massive residential proxy IPs with full JS rendering, geo-targeting, sticky sessions, and device-type targeting.
allowed-tools: Bash(agent-browser:*)
homepage: https://partners.joinmassive.com/create-account-clawpod
metadata: {"openclaw":{"emoji":"🦀","homepage":"https://partners.joinmassive.com/create-account-clawpod","requires":{"bins":["agent-browser"],"env":["MASSIVE_PROXY_USERNAME","MASSIVE_PROXY_PASSWORD"]},"primaryEnv":"MASSIVE_PROXY_USERNAME","install":[{"id":"node","kind":"node","package":"agent-browser","bins":["agent-browser"],"label":"Install agent-browser (npm)"}]}}
---

# ClawPod

Browse and fetch web pages through residential proxy IPs via the Massive network. Uses [agent-browser](https://github.com/vercel-labs/agent-browser) (Playwright/Chromium) for full JavaScript rendering, real browser fingerprints, screenshots, and page interaction — all routed through Massive residential proxies.

---

## Setup

### 1. Install agent-browser

```bash
npm install -g agent-browser
agent-browser install          # downloads bundled Chromium
```

On Linux (including Docker), install system dependencies too:

```bash
agent-browser install --with-deps
```

### 2. Add Massive proxy credentials

Sign up at [Massive](https://partners.joinmassive.com/create-account-clawpod) and get your proxy credentials from the dashboard. Set your credentials as environment variables:

```bash
export MASSIVE_PROXY_USERNAME="your-username"
export MASSIVE_PROXY_PASSWORD="your-password"
```

---

## Core Workflow

Every ClawPod task follows this pattern:

### Step 1: Build the proxy URL

Construct a proxy URL with your Massive credentials. The username must be URL-encoded (see [Proxy URL Format](#proxy-url-format) below).

```bash
# No geo-targeting (any residential IP)
PROXY_URL="https://${MASSIVE_PROXY_USERNAME}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"
```

### Step 2: Open the target page

```bash
agent-browser --proxy "$PROXY_URL" open "https://example.com"
```

This launches a headless Chromium browser, routes traffic through the Massive proxy, navigates to the URL, and waits for the page to load (including JavaScript rendering).

### Step 3: Extract content

```bash
# Get the full page text
agent-browser get text body

# Get an accessibility snapshot (best for structured data)
agent-browser snapshot -i

# Take a screenshot
agent-browser screenshot page.png

# Get page HTML
agent-browser get html
```

### Step 4: Close when done

```bash
agent-browser close
```

**Important:** The `--proxy` flag is a launch-time option. It only takes effect when the browser daemon starts (on the first `open` command). If you need to change the proxy URL (e.g., different geo-targeting), you must `agent-browser close` first, then re-open with the new proxy URL.

---

## Proxy URL Format

Massive encodes geo-targeting, sticky sessions, and device-type parameters in the **proxy username** using query-string syntax:

```
raw username:   myuser?country=US&city=New York
```

For the `--proxy` URL, **the username must be percent-encoded** because `?`, `=`, `&`, and spaces are special characters in URLs:

```
encoded:        myuser%3Fcountry%3DUS%26city%3DNew%20York
```

Full proxy URL:

```
https://myuser%3Fcountry%3DUS%26city%3DNew%20York:mypassword@network.joinmassive.com:65535
```

### Encoding rules

| Character | Encoded | Why |
|-----------|---------|-----|
| `?` | `%3F` | Separates username from params |
| `=` | `%3D` | Separates param key from value |
| `&` | `%26` | Separates multiple params |
| ` ` (space) | `%20` | Spaces in city names etc. |

### Building the proxy URL in bash

```bash
# No geo-targeting
PROXY_URL="https://${MASSIVE_PROXY_USERNAME}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"

# With geo-targeting — encode the username
ENCODED_USER=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${MASSIVE_PROXY_USERNAME}?country=US&city=New York', safe=''))")
PROXY_URL="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"
```

Or encode manually:

```bash
ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fcountry%3DUS%26city%3DNew%20York"
PROXY_URL="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"
```

---

## Geo-Targeting

Add geo-targeting parameters to the proxy username. All parameters are optional.

| Parameter | Description | Example values |
|-----------|-------------|----------------|
| `country` | ISO 3166-1 alpha-2 country code | `US`, `GB`, `DE`, `FR` |
| `city` | City name (English) | `New York`, `London`, `Berlin` |
| `subdivision` | State or subdivision code | `CA`, `TX`, `NY` |
| `zipcode` | Zipcode | `10001`, `90210` |

**Rules:**
- `country` is required when using any other geo parameter
- Country + city is more reliable than zipcode
- If both `subdivision` and `zipcode` are specified, `city` is ignored
- Overly narrow constraints may fail — relax parameters if needed

### Examples

```bash
# Any IP in Germany
ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fcountry%3DDE"

# IP in New York City
ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fcountry%3DUS%26city%3DNew%20York%26subdivision%3DNY"

# IP in a specific US zipcode
ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fcountry%3DUS%26zipcode%3D90210"

# IP in London
ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fcountry%3DGB%26city%3DLondon"
```

Then use: `PROXY_URL="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"`

---

## Sticky Sessions

Route multiple requests through the **same exit IP**. Add session parameters to the proxy username.

| Parameter | Description | Default |
|-----------|-------------|---------|
| `session` | Session ID (up to 255 chars) | *(none)* |
| `sessionttl` | TTL in minutes (1-240) | 15 |
| `sessionmode` | `strict` or `flex` | `strict` |

**Modes:**
- **strict** (default): any proxy error invalidates the session and rotates to a new IP
- **flex**: tolerates transient errors — session persists until too many consecutive failures

**Important:** Session TTL is static — expires at creation time + TTL, not extended by subsequent requests. Changing geo parameters creates a different session.

### Example

```bash
# Sticky session with 30-minute TTL
ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fsession%3Dmysession1%26sessionttl%3D30%26sessionmode%3Dflex"
PROXY_URL="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"
agent-browser --proxy "$PROXY_URL" open "https://example.com"
```

**Important:** Since `--proxy` is a launch-time option, the sticky session is locked for the lifetime of the browser daemon. All pages opened in the same daemon session use the same proxy configuration. To change sessions, close and reopen:

```bash
agent-browser close
agent-browser --proxy "$NEW_PROXY_URL" open "https://example.com/page2"
```

---

## Device-Type Targeting

Route through specific device types by adding the `type` parameter.

| Value | Description |
|-------|-------------|
| `mobile` | Mobile device IPs |
| `common` | Desktop/laptop IPs |
| `tv` | Smart TV IPs |

### Example

```bash
# Mobile IP in the US
ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Ftype%3Dmobile%26country%3DUS"
PROXY_URL="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"
agent-browser --proxy "$PROXY_URL" open "https://example.com"
```

---

## Common Patterns

### Fetch a page and get its text

```bash
PROXY_URL="https://${MASSIVE_PROXY_USERNAME}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"
agent-browser --proxy "$PROXY_URL" open "https://example.com"
agent-browser get text body
agent-browser close
```

### Fetch a JS-rendered page (SPA)

agent-browser renders JavaScript automatically — no special flags needed:

```bash
agent-browser --proxy "$PROXY_URL" open "https://spa-site.com/dashboard"
agent-browser snapshot -i          # interactive elements after JS renders
agent-browser close
```

### Take a screenshot

```bash
agent-browser --proxy "$PROXY_URL" open "https://example.com"
agent-browser screenshot page.png
agent-browser close
```

### Full-page screenshot

```bash
agent-browser --proxy "$PROXY_URL" open "https://example.com"
agent-browser screenshot --full fullpage.png
agent-browser close
```

### Extract structured data with accessibility snapshot

```bash
agent-browser --proxy "$PROXY_URL" open "https://example.com"
agent-browser snapshot -i -c       # interactive + compact
agent-browser close
```

### Verify exit IP and geo-targeting

```bash
ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fcountry%3DDE"
PROXY_URL="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"
agent-browser --proxy "$PROXY_URL" open "https://httpbin.org/ip"
agent-browser get text body             # should show a German residential IP
agent-browser close
```

### Multi-page session (sticky IP)

```bash
ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fsession%3Dcrawl1%26sessionttl%3D60"
PROXY_URL="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"
agent-browser --proxy "$PROXY_URL" open "https://example.com/page1"
agent-browser get text body
agent-browser open "https://example.com/page2"    # same proxy, same IP
agent-browser get text body
agent-browser close
```

---

## Important Notes

- **Credentials required:** `MASSIVE_PROXY_USERNAME` and `MASSIVE_PROXY_PASSWORD` must be set as environment variables.
- **Browser startup latency:** The first `open` command takes 3-8 seconds as Chromium launches. Subsequent `open` commands within the same session are faster.
- **Proxy is launch-time only:** The `--proxy` flag only applies when the browser daemon starts. To change proxy settings, `agent-browser close` first, then reopen.
- **URL encoding is critical:** The proxy username with geo-targeting params must be percent-encoded in the proxy URL. Unencoded `?`, `=`, `&`, or spaces will break the URL.
- **JS rendering is automatic:** Unlike raw HTTP fetching, agent-browser renders JavaScript, executes the page, and handles redirects and cookies automatically.
- **Real browser fingerprint:** Requests use a real Chromium browser fingerprint, making them much harder to detect as automated.
- **One browser at a time:** The agent-browser daemon manages one browser instance. Use `close` between different proxy configurations.

---

## Links

- [agent-browser](https://github.com/vercel-labs/agent-browser) — Playwright/Chromium CLI for AI agents
- [Massive](https://joinmassive.com) — Residential proxy network
- [Massive Portal](https://partners.joinmassive.com/create-account-clawpod) — Sign up and manage credentials
