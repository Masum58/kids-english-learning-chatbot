"""End-to-end latency measurement. Usage:
    python scripts/measure_latency.py --url http://localhost:8000
    python scripts/measure_latency.py --url https://<live-url> --n 50 --llm-n 10
"""
import argparse
import statistics
import time

import httpx

SCENARIOS = [
    # (name, message, uses_llm)
    ("Greeting (rules)", "hi", False),
    ("Learning (rules)", "teach me animals", False),
    ("Support, stuck (rules)", "I don't know", False),
    ("Engagement (rules)", "let's play a game", False),
    ("Support, emotion (LLM)", "I am sad", True),
    ("Conversation (LLM)", "Why is the sky blue?", True),
]


def percentile(values: list[float], p: float) -> float:
    s = sorted(values)
    return s[min(len(s) - 1, int(len(s) * p / 100))]


def run(client: httpx.Client, base: str, message: str, n: int, delay: float):
    wall, server, llm_hits, errors = [], [], 0, 0
    for _ in range(n):
        start = time.perf_counter()
        try:
            r = client.post(f"{base}/chat", json={"session_id": None, "message": message})
            elapsed = (time.perf_counter() - start) * 1000
            r.raise_for_status()
            data = r.json()
            wall.append(elapsed)
            server.append(data["latency_ms"])
            llm_hits += bool(data["llm_used"])
        except Exception:
            errors += 1
        if delay:
            time.sleep(delay)
    return wall, server, llm_hits, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--n", type=int, default=30, help="requests per rule-based scenario")
    ap.add_argument("--llm-n", type=int, default=10, help="requests per LLM scenario")
    ap.add_argument("--llm-delay", type=float, default=5.0, help="seconds between LLM calls (free-tier rate limit)")
    args = ap.parse_args()
    base = args.url.rstrip("/")

    with httpx.Client(timeout=10) as client:
        client.get(f"{base}/health")                       # cold start jagai
        print(f"Target: {base}\n")
        print("| Scenario | n | p50 (ms) | p95 (ms) | max (ms) | server p50 (ms) | LLM used | errors |")
        print("|---|---|---|---|---|---|---|---|")
        worst = 0.0
        for name, message, uses_llm in SCENARIOS:
            n = args.llm_n if uses_llm else args.n
            wall, server, llm_hits, errors = run(client, base, message, n, args.llm_delay if uses_llm else 0)
            if not wall:
                print(f"| {name} | {n} | - | - | - | - | - | {errors} |")
                continue
            worst = max(worst, max(wall))
            print(f"| {name} | {n} | {statistics.median(wall):.0f} | {percentile(wall, 95):.0f} | "
                  f"{max(wall):.0f} | {statistics.median(server):.0f} | {llm_hits}/{len(wall)} | {errors} |")
        print(f"\nSlowest request: {worst:.0f} ms ->", "PASS (< 2000 ms)" if worst < 2000 else "CHECK (>= 2000 ms)")


if __name__ == "__main__":
    main()