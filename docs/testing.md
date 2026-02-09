 ClawPod v0.1 — Testing Plan

 Context

 Implementation is complete (4 files created). Credentials are configured. Need to verify the live proxy works end-to-end: basic fetch, geo-targeting, HTTP vs HTTPS, POST, error handling, and body formatting.

 ---
 Test Commands (run sequentially)

 1. Basic HTTPS fetch — verify residential IP

 python3 scripts/fetch.py -u "https://httpbin.org/ip"
 Expect: JSON with status: 200, body showing a residential IP (not your real IP).

 2. Basic HTTP fetch — verify HTTP proxy path works

 python3 scripts/fetch.py -u "http://httpbin.org/ip"
 Expect: Same structure, residential IP. Confirms the non-CONNECT HTTP proxy code path.

 3. Geo-targeting — country

 python3 scripts/fetch.py -u "https://httpbin.org/ip" --country DE
 Expect: status: 200, IP should geolocate to Germany.

 4. Geo-targeting — country + city + state

 python3 scripts/fetch.py -u "https://httpbin.org/ip" --country US --city "New York" --state NY
 Expect: status: 200, IP should geolocate to New York area.

 5. POST with JSON body

 python3 scripts/fetch.py -u "https://httpbin.org/post" -m POST -d '{"key":"value"}' -H "Content-Type: application/json"
 Expect: status: 200, body contains the echoed POST data (httpbin mirrors it back). Body should be pretty-printed JSON.

 6. Custom headers

 python3 scripts/fetch.py -u "https://httpbin.org/headers" -H "X-Custom-Test: hello123"
 Expect: status: 200, body shows X-Custom-Test: hello123 in the headers echo.

 7. JSON pretty-print verification

 python3 scripts/fetch.py -u "https://httpbin.org/json"
 Expect: status: 200, body is indented/pretty-printed JSON (not a single-line blob).

 8. Error handling — invalid URL

 python3 scripts/fetch.py -u "https://this-domain-does-not-exist-xyz123.com"
 Expect: JSON error with "DNS resolution failed", status: null.

 9. Error handling — non-existent page (404)

 python3 scripts/fetch.py -u "https://httpbin.org/status/404"
 Expect: status: 404 — should return the response, NOT an error object (4xx/5xx are valid responses).

 10. JSON output validity — pipe every test through jq

 python3 scripts/fetch.py -u "https://httpbin.org/ip" | python3 -m json.tool > /dev/null && echo "VALID JSON"
 Expect: "VALID JSON" — confirms output is parseable.

 ---
 What to Look For

 - All output is valid JSON (pipe through python3 -m json.tool)
 - HTTPS and HTTP both work (tests 1 and 2)
 - Geo-targeting changes the IP location (tests 3 and 4)
 - POST data and custom headers are sent correctly (tests 5 and 6)
 - JSON responses are pretty-printed in the body (test 7)
 - DNS errors produce clean JSON errors, not tracebacks (test 8)
 - HTTP 4xx/5xx are returned as responses, not errors (test 9)