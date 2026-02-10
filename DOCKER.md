# Docker Testing

Run ClawPod's full test suite in an isolated Docker sandbox. The container includes Chromium and agent-browser for end-to-end proxy testing.

## Prerequisites

- Docker and Docker Compose
- Massive proxy credentials ([sign up](https://partners.joinmassive.com/create-account-clawpod))

## Quick Start

```bash
# 1. Create your .env (never enters the Docker image)
cp .env.example .env

# 2. Add your Massive proxy credentials
#    Edit .env with your username and password

# 3. Build and run all tests
docker compose run --rm clawpod-test
```

## What the Tests Cover

| # | Test | Checks |
|---|------|--------|
| 1 | Basic proxy fetch | Open page via proxy, extract IP address |
| 2 | Geo-targeting (country) | `country=DE` returns IP through proxy |
| 3 | Geo-targeting (multi-param) | `country=US`, `city=New York`, `subdivision=NY` |
| 4 | JS rendering | Page content rendered after JavaScript execution |
| 5 | Screenshot | Capture page as PNG file |
| 6 | Accessibility snapshot | Interactive elements extracted from form page |
| 7 | Multi-page navigation | Two pages in same daemon session |

## Common Commands

```bash
# Run all tests
docker compose run --rm clawpod-test

# Interactive shell
docker compose run --rm clawpod-test bash

# Rebuild after code changes
docker compose build
```

## Resource Requirements

Running Chromium in Docker requires more resources than the previous Python-only approach:

| Resource | Value | Why |
|----------|-------|-----|
| Memory | 1 GB | Chromium needs ~300-500 MB |
| /tmp tmpfs | 256 MB | Browser temp files |
| /dev/shm tmpfs | 256 MB | Chromium shared memory |
| PIDs | 256 | Chromium spawns multiple processes |
| Image size | ~700 MB | Includes Chromium + system libs |

## Security Model

The container is isolated from the host:

- **No volume mounts** — everything is COPY'd at build time
- **Read-only root filesystem** — only `/tmp` and `/dev/shm` are writable
- **Non-root user** — runs as `appuser` (uid 1000)
- **All capabilities dropped** — `cap_drop: ALL`
- **No privilege escalation** — `no-new-privileges`
- **Memory limited** — 1 GB max
- **PID limited** — 256 processes max
- **Credentials as env vars only** — never written to disk or baked into image layers

## Troubleshooting

**"Missing Massive proxy credentials"**
Your `.env` file is missing or doesn't have both `MASSIVE_PROXY_USERNAME` and `MASSIVE_PROXY_PASSWORD`. Copy `.env.example` and fill in your credentials.

**"Proxy authentication failed"**
Credentials are invalid. Verify them at [partners.joinmassive.com](https://partners.joinmassive.com/login).

**Build fails with "COPY failed"**
Make sure you're running `docker compose build` from the repo root (where `Dockerfile` lives).

**"read-only file system" errors**
Expected behavior — the container's root filesystem is read-only by design. Only `/tmp` and `/dev/shm` are writable.

**Chromium crashes or "no usable sandbox"**
The container uses `--no-sandbox` by default via Playwright. If Chromium still crashes, check that `/dev/shm` tmpfs is mounted and memory limit is sufficient (1 GB minimum).
