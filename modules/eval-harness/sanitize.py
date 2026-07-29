#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sanitize.py - turn a PRIVATE fleet consensus ledger into a PUBLIC, shippable fixture.

WHY (methodology, not decoration): the benchmark must run on REAL fleet traces, not
synthetic data - that is the whole point of "reproducible evals": a benchmark you cannot
re-run on real data is a screenshot, not a measurement. But the
raw ledger names real machines and carries operational free-text (paths, serials, keys,
signatures). The invariants this harness scores are STRUCTURAL - they read only event type,
actor, timestamp, risk tier and the proposal they belong to. So we project every event onto a
strict field WHITELIST and drop all free-text payload (subject/details/proof/sig/signer).
Result: the real causal shape - who did what, in what order, under which risk tier - is
preserved byte-for-byte; zero operational text ships. Sanitization is deterministic and the
drop is total, so there is nothing to leak and nothing to audit line-by-line.

Deterministic: same input -> same output (no randomness), so the fixture is reproducible.

Usage:
    python sanitize.py <ledger_dir> <out_fixture.jsonl>
    # ledger_dir = folder of log-<MACHINE>.jsonl shards (single-writer append-only)
"""
import os, sys, json, re, glob, hashlib

# Role map: YOUR hostnames -> generic fleet roles ("hub", "laptop-1", ...).
# Loaded from rolemap.json next to this script (see rolemap.example.json). It is deliberately NOT
# hardcoded: a machine name is exactly the kind of identifier this script exists to remove, so it
# has no business living in the source of a tool other people run. Keep your rolemap.json local
# (it is gitignored). Any host missing from the map still never leaks: it becomes a deterministic
# anon-<hash> id.
def _load_role_map():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rolemap.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"[sanitize] warning: could not read rolemap.json ({e}); using anon ids only")
        return {}


ROLE_MAP = _load_role_map()

# the ONLY fields the eval reads. Everything else (subject/details/proof/sig/signer/text) is
# free-text operational payload and is dropped entirely - never shipped.
KEEP_FIELDS = ("event_id", "proposal_id", "type", "actor", "ts", "risk_tier", "reversible")


def anon_actor(name):
    if name in ROLE_MAP:
        return ROLE_MAP[name]
    if name and name.startswith("tg-"):
        base = name[3:]
        return "tg-" + ROLE_MAP.get(base, "anon-" + hashlib.sha1(base.encode()).hexdigest()[:6])
    if not name:
        return "unknown"
    return "anon-" + hashlib.sha1(name.encode()).hexdigest()[:6]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    ledger_dir, out_path = sys.argv[1], sys.argv[2]
    shards = sorted(glob.glob(os.path.join(ledger_dir, "log-*.jsonl")))
    # ignore tg-* mirror shards (duplicate the primary rail) so we don't double-count events
    shards = [s for s in shards if not os.path.basename(s).startswith("log-tg-")]
    seen_event_ids = set()
    rows, touched = [], 0
    for s in shards:
        for ln in open(s, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                e = json.loads(ln)
            except Exception:
                continue
            eid = e.get("event_id")
            if eid and eid in seen_event_ids:
                continue          # idempotent across redundant multi-rail delivery
            if eid:
                seen_event_ids.add(eid)
            # project onto the whitelist: keep structural fields, drop all free-text payload
            row = {k: e[k] for k in KEEP_FIELDS if k in e}
            row["actor"] = anon_actor(e.get("actor"))
            dropped = [k for k in e if k not in KEEP_FIELDS]
            if dropped:
                touched += 1
            rows.append(row)
    rows.sort(key=lambda r: (r.get("proposal_id", ""), r.get("ts", "")))
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[sanitize] shards={len(shards)} events={len(rows)} scrubbed={touched} -> {out_path}")


if __name__ == "__main__":
    main()
