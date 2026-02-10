#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# ClawPod Test Runner (agent-browser)
# Tests proxy connectivity, geo-targeting, JS rendering, and screenshots
# =============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0
TOTAL=0

pass() {
    PASSED=$((PASSED + 1))
    TOTAL=$((TOTAL + 1))
    echo -e "  ${GREEN}PASS${NC} $1"
}

fail() {
    FAILED=$((FAILED + 1))
    TOTAL=$((TOTAL + 1))
    echo -e "  ${RED}FAIL${NC} $1"
    if [ -n "${2:-}" ]; then
        echo -e "       ${RED}$2${NC}"
    fi
}

header() {
    echo ""
    echo -e "${YELLOW}[$1] $2${NC}"
}

cleanup() {
    agent-browser close 2>/dev/null || true
}

# Always clean up on exit
trap cleanup EXIT

# =============================================================================
# Pre-flight: Check credentials
# =============================================================================
if [ -z "${MASSIVE_PROXY_USERNAME:-}" ] || [ -z "${MASSIVE_PROXY_PASSWORD:-}" ]; then
    echo -e "${RED}ERROR: Missing Massive proxy credentials${NC}"
    echo "Set MASSIVE_PROXY_USERNAME and MASSIVE_PROXY_PASSWORD in .env"
    exit 1
fi

# =============================================================================
# Build proxy URL (no geo-targeting)
# =============================================================================
PROXY_URL="https://${MASSIVE_PROXY_USERNAME}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"

# =============================================================================
# Test 1: Basic proxy fetch — verify we get an IP through the proxy
# =============================================================================
header "1" "Basic proxy fetch — http://ip-api.com/json"

cleanup
OUTPUT=$(agent-browser --proxy "$PROXY_URL" open "http://ip-api.com/json" 2>&1) || true
TEXT=$(agent-browser snapshot 2>&1) || TEXT=""
cleanup

if echo "$TEXT" | grep -qE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'; then
    pass "got IP address through proxy"
else
    fail "no IP address in response" "$TEXT"
fi

if echo "$TEXT" | grep -qi 'success'; then
    pass "ip-api returned success status"
else
    fail "ip-api did not return success" "$TEXT"
fi

# =============================================================================
# Test 2: Geo-targeting — country=DE, verify countryCode
# =============================================================================
header "2" "Geo-targeting — country=DE"

ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fcountry%3DDE"
GEO_PROXY="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"

cleanup
OUTPUT=$(agent-browser --proxy "$GEO_PROXY" open "http://ip-api.com/json" 2>&1) || true
TEXT=$(agent-browser snapshot 2>&1) || TEXT=""
cleanup

if echo "$TEXT" | grep -qE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'; then
    pass "got IP address with country=DE"
else
    fail "no IP address in geo-targeted response" "$TEXT"
fi

if echo "$TEXT" | grep -qi 'Germany\|"DE"'; then
    pass "country is Germany (DE)"
else
    fail "country is not Germany" "$TEXT"
fi

# =============================================================================
# Test 3: Geo-targeting — country=US, city=New York, subdivision=NY
# =============================================================================
header "3" "Geo-targeting — country=US, city=New York, subdivision=NY"

ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fcountry%3DUS%26city%3DNew%20York%26subdivision%3DNY"
GEO_PROXY="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"

cleanup
OUTPUT=$(agent-browser --proxy "$GEO_PROXY" open "http://ip-api.com/json" 2>&1) || true
TEXT=$(agent-browser snapshot 2>&1) || TEXT=""
cleanup

if echo "$TEXT" | grep -qE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'; then
    pass "got IP address with US/NY geo-targeting"
else
    fail "no IP address in multi-param geo-targeted response" "$TEXT"
fi

if echo "$TEXT" | grep -qi 'United States\|"US"'; then
    pass "country is United States (US)"
else
    fail "country is not United States" "$TEXT"
fi

# =============================================================================
# Test 4: JS rendering — fetch a page that requires JavaScript
# =============================================================================
header "4" "JS rendering — page content after JavaScript execution"

cleanup
OUTPUT=$(agent-browser --proxy "$PROXY_URL" open "https://httpbin.org/html" 2>&1) || true
TEXT=$(agent-browser snapshot 2>&1) || TEXT=""
cleanup

if [ -n "$TEXT" ] && [ ${#TEXT} -gt 50 ]; then
    pass "got rendered page content (${#TEXT} chars)"
else
    fail "page content empty or too short" "$TEXT"
fi

# =============================================================================
# Test 5: Screenshot
# =============================================================================
header "5" "Screenshot — capture page as PNG"

cleanup
OUTPUT=$(agent-browser --proxy "$PROXY_URL" open "http://ip-api.com/json" 2>&1) || true
SCREENSHOT_OUTPUT=$(agent-browser screenshot /tmp/test_screenshot.png 2>&1) || SCREENSHOT_OUTPUT=""
cleanup

if [ -f /tmp/test_screenshot.png ] && [ -s /tmp/test_screenshot.png ]; then
    pass "screenshot saved to /tmp/test_screenshot.png"
    rm -f /tmp/test_screenshot.png
else
    fail "screenshot file not created or empty" "$SCREENSHOT_OUTPUT"
fi

# =============================================================================
# Test 6: Accessibility snapshot
# =============================================================================
header "6" "Accessibility snapshot — interactive elements"

cleanup
OUTPUT=$(agent-browser --proxy "$PROXY_URL" open "https://httpbin.org/forms/post" 2>&1) || true
SNAPSHOT=$(agent-browser snapshot -i 2>&1) || SNAPSHOT=""
cleanup

if [ -n "$SNAPSHOT" ] && [ ${#SNAPSHOT} -gt 10 ]; then
    pass "got accessibility snapshot (${#SNAPSHOT} chars)"
else
    fail "accessibility snapshot empty or too short" "$SNAPSHOT"
fi

# =============================================================================
# Test 7: Multi-page navigation (same daemon session)
# =============================================================================
header "7" "Multi-page navigation — two pages, same proxy session"

cleanup
OUTPUT=$(agent-browser --proxy "$PROXY_URL" open "http://ip-api.com/json" 2>&1) || true
TEXT1=$(agent-browser snapshot 2>&1) || TEXT1=""
OUTPUT=$(agent-browser open "https://httpbin.org/headers" 2>&1) || true
TEXT2=$(agent-browser snapshot 2>&1) || TEXT2=""
cleanup

if echo "$TEXT1" | grep -qE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'; then
    pass "first page returned IP"
else
    fail "first page did not return IP" "$TEXT1"
fi

if [ -n "$TEXT2" ] && [ ${#TEXT2} -gt 10 ]; then
    pass "second page returned content"
else
    fail "second page content empty" "$TEXT2"
fi

# =============================================================================
# Test 8: Sticky session — same IP across browser restart
# =============================================================================
header "8" "Sticky session — same IP across browser restart"

ENCODED_USER="${MASSIVE_PROXY_USERNAME}%3Fsession%3Dtest-$$%26sessionttl%3D5"
STICKY_PROXY="https://${ENCODED_USER}:${MASSIVE_PROXY_PASSWORD}@network.joinmassive.com:65535"

cleanup
OUTPUT=$(agent-browser --proxy "$STICKY_PROXY" open "http://ip-api.com/json" 2>&1) || true
SNAP1=$(agent-browser snapshot 2>&1) || SNAP1=""
IP1=$(echo "$SNAP1" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -1) || IP1=""
cleanup

OUTPUT=$(agent-browser --proxy "$STICKY_PROXY" open "http://ip-api.com/json" 2>&1) || true
SNAP2=$(agent-browser snapshot 2>&1) || SNAP2=""
IP2=$(echo "$SNAP2" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -1) || IP2=""
cleanup

if [ -n "$IP1" ] && [ -n "$IP2" ]; then
    pass "got IPs from both requests ($IP1, $IP2)"
    if [ "$IP1" = "$IP2" ]; then
        pass "sticky session maintained same IP"
    else
        fail "IPs differ across sticky session" "first=$IP1 second=$IP2"
    fi
else
    fail "could not get IPs for sticky session test" "ip1='$IP1' ip2='$IP2'"
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "==========================================="
if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}ALL $TOTAL CHECKS PASSED${NC}"
else
    echo -e "${RED}$FAILED/$TOTAL CHECKS FAILED${NC} (${GREEN}$PASSED passed${NC})"
fi
echo "==========================================="

if [ "$FAILED" -gt 0 ]; then
    exit 1
fi
