#!/usr/bin/env -S python3 -u
"""
ClawPod — Fetch web pages through Massive residential proxy IPs.

Sends HTTP/HTTPS requests through the Massive proxy network with optional
geo-targeting by country, city, state, or zipcode. Stdlib only — no pip
dependencies.
"""

import argparse
import base64
import json
import os
import socket
import ssl
import sys
import urllib.parse
from pathlib import Path


# =============================================================================
# Auto-load .env files
# =============================================================================
def _load_env_file(env_path):
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    if line.startswith("export "):
                        line = line[7:]
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value


_skill_dir = Path(__file__).resolve().parent.parent
_load_env_file(_skill_dir.parent / ".env")   # ~/.openclaw/.env
_load_env_file(_skill_dir / ".env")           # ~/.openclaw/skills/clawpod/.env


# =============================================================================
# Constants
# =============================================================================
PROXY_HOST = "network.joinmassive.com"
PROXY_PORT = 65535

CONNECT_TIMEOUT = 10   # seconds
READ_TIMEOUT = 30      # seconds
TOTAL_TIMEOUT = 60     # seconds

MAX_BODY_SIZE = 500 * 1024  # 500 KB

USER_AGENT = "Mozilla/5.0 (compatible; ClawPod/0.1)"


# =============================================================================
# Credentials
# =============================================================================
def get_credentials():
    username = os.environ.get("MASSIVE_PROXY_USERNAME")
    password = os.environ.get("MASSIVE_PROXY_PASSWORD")
    if not username or not password:
        print(json.dumps({
            "error": "Missing Massive proxy credentials",
            "how_to_fix": [
                "1. Sign up at https://app.joinmassive.com and purchase a residential proxy plan",
                "2. Get your proxy username and password from the dashboard",
                '3. Add to ~/.openclaw/.env or ~/.openclaw/skills/clawpod/.env:',
                '   MASSIVE_PROXY_USERNAME="your-username"',
                '   MASSIVE_PROXY_PASSWORD="your-password"',
            ],
        }, indent=2), flush=True)
        sys.exit(1)
    return username, password


# =============================================================================
# Proxy username with geo-targeting
# =============================================================================
def build_proxy_username(username, country=None, city=None, state=None, zipcode=None):
    params = {}
    if country:
        params["country"] = country
    if city:
        params["city"] = city
    if state:
        params["state"] = state
    if zipcode:
        params["zipcode"] = zipcode
    if params:
        return username + "?" + urllib.parse.urlencode(params)
    return username


# =============================================================================
# HTTPS CONNECT tunnel
# =============================================================================
def _tls_connect_to_proxy(proxy_host, proxy_port):
    """Establish a TLS connection to the proxy server itself."""
    raw_sock = socket.create_connection((proxy_host, proxy_port), timeout=CONNECT_TIMEOUT)
    raw_sock.settimeout(READ_TIMEOUT)
    proxy_ctx = ssl.create_default_context()
    return proxy_ctx.wrap_socket(raw_sock, server_hostname=proxy_host)


class _TLSinTLSSocket:
    """Wraps an ssl.SSLObject (via MemoryBIO) to look like a socket.

    Python's ssl.wrap_socket cannot layer TLS on top of an existing TLS
    socket.  MemoryBIO + wrap_bio solves this: we shuttle encrypted bytes
    between the inner SSLObject and the outer proxy TLS socket manually.
    """

    def __init__(self, ssl_obj, proxy_tls):
        self._ssl = ssl_obj
        self._proxy = proxy_tls
        self._out = ssl_obj  # wrap_bio's outgoing BIO is internal
        # We keep references to the BIOs via the connect_via_proxy closure.

    # -- public socket-like API used by send_request / read_response --------

    def sendall(self, data):
        self._ssl.write(data)
        self._flush_outgoing()

    def recv(self, bufsize):
        while True:
            try:
                return self._ssl.read(bufsize)
            except ssl.SSLWantReadError:
                raw = self._proxy.recv(16384)
                if not raw:
                    return b""
                self._incoming.write(raw)

    def settimeout(self, t):
        self._proxy.settimeout(t)

    def close(self):
        self._proxy.close()

    def _flush_outgoing(self):
        data = self._outgoing.read()
        if data:
            self._proxy.sendall(data)


def connect_via_proxy(proxy_host, proxy_port, target_host, target_port, username, password):
    """Establish HTTPS connection through TLS-encrypted CONNECT proxy."""
    proxy_tls = _tls_connect_to_proxy(proxy_host, proxy_port)

    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    connect_req = (
        f"CONNECT {target_host}:{target_port} HTTP/1.1\r\n"
        f"Host: {target_host}:{target_port}\r\n"
        f"Proxy-Authorization: Basic {auth}\r\n"
        f"\r\n"
    )
    proxy_tls.sendall(connect_req.encode())

    response = b""
    while b"\r\n\r\n" not in response:
        chunk = proxy_tls.recv(4096)
        if not chunk:
            proxy_tls.close()
            raise Exception("Proxy closed connection during CONNECT")
        response += chunk

    status_line = response.split(b"\r\n")[0].decode()
    status_code = int(status_line.split()[1])
    if status_code == 407:
        proxy_tls.close()
        raise ProxyAuthError("Proxy authentication failed (407). Check MASSIVE_PROXY_USERNAME and MASSIVE_PROXY_PASSWORD.")
    if status_code == 502:
        proxy_tls.close()
        raise Exception(f"DNS resolution failed: proxy returned 502 for {target_host}")
    if status_code != 200:
        proxy_tls.close()
        raise Exception(f"Proxy CONNECT failed: {status_line}")

    # TLS-in-TLS via MemoryBIO
    incoming = ssl.MemoryBIO()
    outgoing = ssl.MemoryBIO()
    target_ctx = ssl.create_default_context()
    ssl_obj = target_ctx.wrap_bio(incoming, outgoing, server_hostname=target_host)

    # Perform inner TLS handshake
    while True:
        try:
            ssl_obj.do_handshake()
            break
        except ssl.SSLWantReadError:
            # flush outgoing handshake bytes to proxy tunnel
            data = outgoing.read()
            if data:
                proxy_tls.sendall(data)
            # read incoming handshake bytes from proxy tunnel
            data = proxy_tls.recv(16384)
            if data:
                incoming.write(data)

    # Build a socket-like wrapper
    wrapper = _TLSinTLSSocket(ssl_obj, proxy_tls)
    wrapper._incoming = incoming
    wrapper._outgoing = outgoing
    return wrapper


# =============================================================================
# HTTP proxy (non-TLS targets)
# =============================================================================
def connect_http_proxy(proxy_host, proxy_port):
    """Open a TLS connection to the proxy for plain HTTP requests."""
    return _tls_connect_to_proxy(proxy_host, proxy_port)


# =============================================================================
# Custom error types
# =============================================================================
class ProxyAuthError(Exception):
    pass


# =============================================================================
# Build and send raw HTTP request
# =============================================================================
def send_request(sock, method, path, host, headers, body=None):
    """Build a raw HTTP/1.1 request and send it over a socket."""
    lines = [f"{method} {path} HTTP/1.1", f"Host: {host}"]
    for key, value in headers.items():
        lines.append(f"{key}: {value}")
    if body and "Content-Length" not in headers:
        lines.append(f"Content-Length: {len(body.encode('utf-8'))}")
    lines.append("Connection: close")
    lines.append("")
    lines.append("")
    raw = "\r\n".join(lines)
    sock.sendall(raw.encode("utf-8"))
    if body:
        sock.sendall(body.encode("utf-8"))


# =============================================================================
# Parse HTTP response from socket
# =============================================================================
def read_response(sock):
    """Read and parse an HTTP response from a socket. Returns (status, headers_dict, body_bytes)."""
    # Read headers
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk

    if b"\r\n\r\n" not in buf:
        raise Exception("Incomplete HTTP response — no header terminator received")

    header_data, _, body_start = buf.partition(b"\r\n\r\n")
    header_lines = header_data.decode("utf-8", errors="replace").split("\r\n")

    # Parse status line
    status_line = header_lines[0]
    parts = status_line.split(" ", 2)
    status_code = int(parts[1]) if len(parts) >= 2 else 0

    # Parse headers
    headers = {}
    for line in header_lines[1:]:
        if ": " in line:
            key, _, value = line.partition(": ")
            headers[key.lower()] = value

    # Read body
    body = body_start
    content_length = headers.get("content-length")
    transfer_encoding = headers.get("transfer-encoding", "").lower()

    if transfer_encoding == "chunked":
        body = _read_chunked(sock, body)
    elif content_length:
        remaining = int(content_length) - len(body)
        while remaining > 0:
            chunk = sock.recv(min(remaining, 65536))
            if not chunk:
                break
            body += chunk
            remaining -= len(chunk)
            if len(body) > MAX_BODY_SIZE:
                break
    else:
        # Read until connection close
        while len(body) <= MAX_BODY_SIZE:
            try:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                body += chunk
            except socket.timeout:
                break

    return status_code, headers, body


def _read_chunked(sock, initial_data):
    """Read a chunked transfer-encoded body."""
    buf = initial_data
    body = b""

    while True:
        # Ensure we have a full chunk size line
        while b"\r\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                return body
            buf += chunk

        size_line, _, buf = buf.partition(b"\r\n")
        try:
            chunk_size = int(size_line.strip(), 16)
        except ValueError:
            return body

        if chunk_size == 0:
            break

        # Read chunk_size bytes + trailing \r\n
        while len(buf) < chunk_size + 2:
            data = sock.recv(max(chunk_size + 2 - len(buf), 4096))
            if not data:
                body += buf[:chunk_size]
                return body
            buf += data

        body += buf[:chunk_size]
        buf = buf[chunk_size + 2:]  # skip trailing \r\n

        if len(body) > MAX_BODY_SIZE:
            break

    return body


# =============================================================================
# Format response body
# =============================================================================
def format_body(body_bytes, content_type):
    """Format the response body for JSON output."""
    # Detect binary
    try:
        text = body_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return f"[binary content, {len(body_bytes)} bytes]"

    # Truncate if needed
    truncated = False
    if len(body_bytes) > MAX_BODY_SIZE:
        text = text[:MAX_BODY_SIZE]
        truncated = True

    # Pretty-print JSON responses
    if content_type and "application/json" in content_type:
        try:
            parsed = json.loads(text)
            text = json.dumps(parsed, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            pass

    if truncated:
        text += "\n\n[truncated — 500KB limit]"

    return text


# =============================================================================
# Main fetch logic
# =============================================================================
def fetch(url, method="GET", extra_headers=None, body=None,
          country=None, city=None, state=None, zipcode=None):
    """Fetch a URL through the Massive residential proxy. Returns a result dict."""
    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme.lower()
    host = parsed.hostname
    port = parsed.port or (443 if scheme == "https" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    if parsed.fragment:
        path += "#" + parsed.fragment

    if scheme not in ("http", "https"):
        return {"error": f"Unsupported scheme: {scheme}", "url": url, "status": None}

    if not host:
        return {"error": "Invalid URL — no host found", "url": url, "status": None}

    username, password = get_credentials()
    proxy_username = build_proxy_username(username, country, city, state, zipcode)

    # Build request headers
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
    }
    if extra_headers:
        for h in extra_headers:
            if ": " in h:
                key, _, value = h.partition(": ")
                headers[key] = value

    sock = None
    try:
        if scheme == "https":
            sock = connect_via_proxy(PROXY_HOST, PROXY_PORT, host, port, proxy_username, password)
            send_request(sock, method, path, host, headers, body)
        else:
            # HTTP: connect to proxy, send request with full URL as path
            sock = connect_http_proxy(PROXY_HOST, PROXY_PORT)
            auth = base64.b64encode(f"{proxy_username}:{password}".encode()).decode()
            headers["Proxy-Authorization"] = f"Basic {auth}"
            full_url = f"http://{host}:{port}{path}" if port != 80 else f"http://{host}{path}"
            send_request(sock, method, full_url, host, headers, body)

        sock.settimeout(TOTAL_TIMEOUT)
        status_code, resp_headers, body_bytes = read_response(sock)

        # Format body
        content_type = resp_headers.get("content-type", "")
        formatted_body = format_body(body_bytes, content_type)

        # Build clean response headers dict
        clean_headers = {}
        for key, value in resp_headers.items():
            clean_headers[key] = value

        return {
            "url": url,
            "method": method,
            "status": status_code,
            "headers": clean_headers,
            "body": formatted_body,
        }

    except ProxyAuthError as e:
        return {"error": str(e), "url": url, "status": 407}
    except socket.gaierror as e:
        return {"error": f"DNS resolution failed: {e}", "url": url, "status": None}
    except socket.timeout:
        return {"error": "Connection timed out", "url": url, "status": None}
    except ssl.SSLError as e:
        return {"error": f"SSL error: {e}", "url": url, "status": None}
    except ConnectionRefusedError:
        return {"error": "Connection refused by proxy", "url": url, "status": None}
    except OSError as e:
        if e.errno == 65 or "No route to host" in str(e):
            return {"error": "Network unreachable", "url": url, "status": None}
        return {"error": f"Network error: {e}", "url": url, "status": None}
    except Exception as e:
        return {"error": str(e), "url": url, "status": None}
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass


# =============================================================================
# CLI
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="ClawPod — Fetch web pages through Massive residential proxy IPs",
    )
    parser.add_argument("--url", "-u", required=True, help="Target URL to fetch")
    parser.add_argument("--method", "-m", default="GET", help="HTTP method (default: GET)")
    parser.add_argument("--header", "-H", action="append", default=[], help="Extra header as 'Key: Value' (repeatable)")
    parser.add_argument("--data", "-d", default=None, help="Request body (for POST/PUT)")
    parser.add_argument("--country", default=None, help="ISO 3166-1 alpha-2 country code (e.g. US, GB, DE)")
    parser.add_argument("--city", default=None, help="City name for geo-targeting (English)")
    parser.add_argument("--state", default=None, help="State/subdivision code (e.g. CA, TX)")
    parser.add_argument("--zipcode", default=None, help="Zipcode for geo-targeting")

    args = parser.parse_args()

    result = fetch(
        url=args.url,
        method=args.method.upper(),
        extra_headers=args.header,
        body=args.data,
        country=args.country,
        city=args.city,
        state=args.state,
        zipcode=args.zipcode,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
