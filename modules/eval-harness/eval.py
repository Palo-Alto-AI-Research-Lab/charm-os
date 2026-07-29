#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""eval.py - run the invariants over a trace file and emit a scorecard.

This is the whole eval loop: load a JSONL trace -> group events by proposal -> run every
invariant on every proposal -> aggregate pass/fail/n-a -> print a scorecard (+ optional JSON).
Zero tokens, zero network, fully deterministic: the same trace always yields the same score,
which is exactly what makes it a benchmark rather than a demo.

Usage:
    python eval.py <trace.jsonl> [--json out.json]

Exit code = number of FAILED invariant checks (0 = clean), so CI can gate on it.
"""
import sys, json, collections


def load(path):
    """Read a JSONL trace. Skip blank and malformed lines (a live trace may have a half-written
    last line during append) and count them, so a bad line degrades gracefully and VISIBLY
    instead of crashing the whole run."""
    by_prop = collections.defaultdict(list)
    n = skipped = 0
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                e = json.loads(ln)
            except json.JSONDecodeError:
                skipped += 1
                continue
            by_prop[e.get("proposal_id")].append(e)
            n += 1
    return by_prop, n, skipped


def run(path):
    from invariants import INVARIANTS
    by_prop, n_events, skipped = load(path)
    results = {name: collections.Counter() for name, _ in INVARIANTS}
    failures = collections.defaultdict(list)   # invariant -> [(proposal_id, reason)]
    for pid, events in by_prop.items():
        for name, fn in INVARIANTS:
            v = fn(events)
            results[name][v.status] += 1
            if v.status == "fail":
                failures[name].append((pid, v.reason))
    return {
        "trace": path,
        "proposals": len(by_prop),
        "events": n_events,
        "skipped_lines": skipped,
        "invariants": {
            name: {
                "pass": results[name]["pass"],
                "fail": results[name]["fail"],
                "n/a":  results[name]["n/a"],
                "applicable": results[name]["pass"] + results[name]["fail"],
                "pass_rate": (results[name]["pass"] /
                              (results[name]["pass"] + results[name]["fail"]))
                              if (results[name]["pass"] + results[name]["fail"]) else None,
                "failures": failures[name],
            }
            for name, _ in INVARIANTS
        },
    }


def print_scorecard(sc):
    print(f"\n  TRACE: {sc['trace']}")
    line = f"  {sc['proposals']} proposals · {sc['events']} events"
    if sc.get("skipped_lines"):
        line += f" · ⚠ {sc['skipped_lines']} malformed line(s) skipped"
    print(line + "\n")
    if sc["events"] == 0:
        print("  ⚠ no valid events - empty or unreadable trace\n")
    print(f"  {'invariant':<42} {'pass':>5} {'fail':>5} {'n/a':>5} {'rate':>7}")
    print("  " + "-" * 68)
    total_fail = 0
    for name, r in sc["invariants"].items():
        rate = "-" if r["pass_rate"] is None else f"{r['pass_rate']*100:5.1f}%"
        print(f"  {name:<42} {r['pass']:>5} {r['fail']:>5} {r['n/a']:>5} {rate:>7}")
        total_fail += r["fail"]
    print("  " + "-" * 68)
    print(f"  TOTAL FAILED CHECKS: {total_fail}\n")
    for name, r in sc["invariants"].items():
        if r["failures"]:
            print(f"  ✗ {name}")
            for pid, reason in r["failures"][:12]:
                print(f"      {str(pid)[:12]}  {reason}")
            if len(r["failures"]) > 12:
                print(f"      … +{len(r['failures'])-12} more")
    return total_fail


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    path = sys.argv[1]
    try:
        sc = run(path)
    except FileNotFoundError:
        print(f"  error: trace file not found: {path}", file=sys.stderr)
        sys.exit(2)
    total_fail = print_scorecard(sc)
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        json.dump(sc, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"  scorecard -> {out}")
    sys.exit(total_fail)


if __name__ == "__main__":
    main()
