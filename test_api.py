"""
Automated test suite for the Local LLM API.
Tests /health, /generate, and /chat endpoints with response time validation.
"""

import sys
import time
import httpx

FASTAPI_BASE = "http://localhost:8000"
TIMEOUT = 60  # seconds per request

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []


def test_health():
    """Test 1: GET /health"""
    print("\n" + "=" * 60)
    print("TEST 1: Health Check — GET /health")
    print("=" * 60)

    start = time.perf_counter()
    try:
        resp = httpx.get(f"{FASTAPI_BASE}/health", timeout=TIMEOUT)
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"  Status Code : {resp.status_code}")
        print(f"  Response    : {resp.json()}")
        print(f"  Time        : {elapsed_ms:.0f} ms")

        ok = resp.status_code == 200
        results.append(("Health Check", ok, elapsed_ms))
        print(f"  Result      : {PASS if ok else FAIL}")
        return ok
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"  ERROR: {exc}")
        results.append(("Health Check", False, elapsed_ms))
        print(f"  Result      : {FAIL}")
        return False


def test_generate():
    """Test 2: POST /generate"""
    print("\n" + "=" * 60)
    print('TEST 2: Generate — POST /generate {"prompt": "Say hello in 5 words"}')
    print("=" * 60)

    start = time.perf_counter()
    try:
        resp = httpx.post(
            f"{FASTAPI_BASE}/generate",
            json={
                "prompt": "Say hello in 5 words",
                "max_tokens": 50,
                "temperature": 0.7,
            },
            timeout=TIMEOUT,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"  Status Code : {resp.status_code}")
        data = resp.json()
        print(f"  Generated   : {data.get('text', 'N/A')}")
        print(f"  Tokens      : {data.get('tokens_generated', 'N/A')}")
        print(f"  API Time    : {data.get('response_time_ms', 'N/A')} ms")
        print(f"  Total Time  : {elapsed_ms:.0f} ms")

        ok = resp.status_code == 200 and elapsed_ms < 30000
        under_5s = elapsed_ms < 5000
        results.append(("Generate", ok, elapsed_ms))
        print(f"  Under 5s    : {'YES ✅' if under_5s else 'NO ⚠️ (but still passed if under 30s)'}")
        print(f"  Result      : {PASS if ok else FAIL}")
        return ok
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"  ERROR: {exc}")
        results.append(("Generate", False, elapsed_ms))
        print(f"  Result      : {FAIL}")
        return False


def test_chat():
    """Test 3: POST /chat with multi-turn conversation"""
    print("\n" + "=" * 60)
    print("TEST 3: Chat — POST /chat (2-message conversation)")
    print("=" * 60)

    start = time.perf_counter()
    try:
        resp = httpx.post(
            f"{FASTAPI_BASE}/chat",
            json={
                "messages": [
                    {"role": "system", "content": "You are a helpful, concise assistant."},
                    {"role": "user", "content": "What is 2+2? Answer in one word."},
                ],
                "max_tokens": 20,
                "temperature": 0.3,
            },
            timeout=TIMEOUT,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"  Status Code : {resp.status_code}")
        data = resp.json()
        msg = data.get("message", {})
        print(f"  Reply Role  : {msg.get('role', 'N/A')}")
        print(f"  Reply       : {msg.get('content', 'N/A')}")
        print(f"  Tokens      : {data.get('tokens_generated', 'N/A')}")
        print(f"  API Time    : {data.get('response_time_ms', 'N/A')} ms")
        print(f"  Total Time  : {elapsed_ms:.0f} ms")

        ok = resp.status_code == 200 and elapsed_ms < 30000
        under_5s = elapsed_ms < 5000
        results.append(("Chat", ok, elapsed_ms))
        print(f"  Under 5s    : {'YES ✅' if under_5s else 'NO ⚠️ (but still passed if under 30s)'}")
        print(f"  Result      : {PASS if ok else FAIL}")
        return ok
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"  ERROR: {exc}")
        results.append(("Chat", False, elapsed_ms))
        print(f"  Result      : {FAIL}")
        return False


def print_summary():
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    all_pass = True
    for name, passed, ms in results:
        status = PASS if passed else FAIL
        print(f"  {status}  {name:<20} {ms:>8.0f} ms")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED — check output above.")
    print()


if __name__ == "__main__":
    print("🧪 Local LLM API — Automated Test Suite")
    print(f"   Target: {FASTAPI_BASE}")
    print()

    # Run tests
    test_health()
    test_generate()
    test_chat()

    # Summary
    print_summary()

    # Print curl commands for manual testing
    print("=" * 60)
    print("CURL COMMANDS FOR MANUAL TESTING")
    print("=" * 60)
    print()
    print("# Health check")
    print(f'curl {FASTAPI_BASE}/health')
    print()
    print("# Generate text")
    print(f'curl -X POST {FASTAPI_BASE}/generate -H "Content-Type: application/json" -d "{{\\"prompt\\": \\"Explain quantum computing in one sentence\\", \\"max_tokens\\": 100, \\"temperature\\": 0.7}}"')
    print()
    print("# Chat")
    print(f'curl -X POST {FASTAPI_BASE}/chat -H "Content-Type: application/json" -d "{{\\"messages\\": [{{\\"role\\": \\"user\\", \\"content\\": \\"Hello!\\"}}], \\"max_tokens\\": 50}}"')
    print()
    print(f"# Swagger UI: {FASTAPI_BASE}/docs")
    print()

    sys.exit(0 if all(r[1] for r in results) else 1)
