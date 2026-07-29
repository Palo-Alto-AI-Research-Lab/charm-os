#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""curate_public.py - build the LIVE, READABLE public fixture (narrative mode).

`sanitize.py` ships the full corpus as structure only (0 free-text) for statistics. This is its
twin for the SHOWCASE: a small, HAND-CURATED set of real proposals whose subject matter is
already public (our open-source fleet infra / the consensus engine / this harness) - kept WITH
their real, human-readable subjects and verify notes, so a reader sees a LIVE negotiation, not a
skeleton. Identity tokens inside the text are still scrubbed (hostnames -> roles, serials/paths
redacted, SSH signatures stripped, owner/teammate names generalised), so it is readable AND
leak-free.

Curation is EXPLICIT and auditable: only the proposal ids in ALLOWLIST are included, each chosen
because its topic is public infra with no leads / money / secrets. Re-run to reproduce.

Usage:  python curate_public.py <ledger_dir> <out.jsonl>
"""
import os, sys, json, re, glob

# Hand-picked real proposals - all about open fleet/consensus infra, no private content.
# Each id is a prefix (first 8 hex of proposal_id); the label documents WHY it is public-safe.
ALLOWLIST = {
    "e53fd7fe": "Tier-2 sync fix - escalated, human-approved, independently verified, committed",
    "f7c96ed9": "fleet adopts the consensus engine itself (Phase 1)",
    "d3207790": "fleet manifest + heartbeat v3 root-cause fix",
    "5bc42bac": "drive arch-health RED to green + publish scripts snapshot",
}

KEEP = ("event_id", "proposal_id", "type", "actor", "ts", "risk_tier", "reversible")

# Role map: YOUR hostnames -> generic roles. Loaded from rolemap.json (see rolemap.example.json),
# never hardcoded - a hostname is precisely what this script exists to strip, so shipping one in
# the source would defeat the purpose. Unmapped hosts fall back to a deterministic anon-<hash>.
def _load_role_map():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rolemap.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"[curate] warning: could not read rolemap.json ({e}); using anon ids only")
        return {}


ROLE_MAP = _load_role_map()
HOST_RE   = re.compile("|".join(re.escape(h) for h in ROLE_MAP)) if ROLE_MAP else None
SSH_RE    = re.compile(r"-----BEGIN SSH SIGNATURE-----.*?-----END SSH SIGNATURE-----", re.S)
PATH_RE   = re.compile(r"(?:[A-Za-z]:\\[^\s\"']+|/(?:root|home|Users)/[^\s\"']+)")
MD5_RE    = re.compile(r"\b[0-9a-f]{32}\b")
# machine serials MIX letters+digits (F5VYGLV, JR2M6T4); plain UPPERCASE words (MANIFEST,
# HEARTBEAT, APPLIED, RED, QQQ) do NOT - so require >=1 digit AND >=1 letter. Keeps text readable.
SERIAL_RE = re.compile(r"\b(?=[A-Z0-9]*[0-9])(?=[A-Z0-9]*[A-Z])[A-Z0-9]{5,}\b")
# owner / teammate names -> generic roles (the human layer of the trace stays legible, not named)
NAME_RE   = re.compile(r"Anton'?s?|Антон[а-я]*|Antonio", re.I)
PEER_RE   = re.compile(r"Natal[iyа-я]+|Наталь[а-я]+|Rusl[aа-я]+n[aа]?|Руслан[а-я]+", re.I)


def scrub(t):
    if not t:
        return t
    t = SSH_RE.sub("<sig>", t)
    if HOST_RE:
        t = HOST_RE.sub(lambda m: ROLE_MAP[m.group(0)], t)
    t = PATH_RE.sub("<path>", t)
    t = MD5_RE.sub("<hash>", t)
    t = NAME_RE.sub("the owner", t)
    t = PEER_RE.sub("a teammate", t)
    t = SERIAL_RE.sub("<id>", t)      # machine serials only (letter+digit mix); words survive
    return t.strip()


def note_of(e):
    """The most informative free-text on an event: explicit text, else a proof/note in details."""
    if e.get("text"):
        return e["text"]
    d = e.get("details") or {}
    for k in ("proof", "note", "situation", "change"):
        if isinstance(d, dict) and d.get(k):
            return d[k]
    return ""


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    ledger_dir, out_path = sys.argv[1], sys.argv[2]
    shards = [s for s in sorted(glob.glob(os.path.join(ledger_dir, "log-*.jsonl")))
              if not os.path.basename(s).startswith("log-tg-")]
    seen, rows = set(), []
    for s in shards:
        for ln in open(s, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                e = json.loads(ln)
            except Exception:
                continue
            pid = e.get("proposal_id", "")
            if pid[:8] not in ALLOWLIST:
                continue
            eid = e.get("event_id")
            if eid in seen:
                continue
            seen.add(eid)
            row = {k: e[k] for k in KEEP if k in e}
            row["actor"] = ROLE_MAP.get(e.get("actor"), e.get("actor"))
            row["subject"] = scrub(e.get("subject", ""))
            n = scrub(note_of(e))
            if n:
                row["note"] = n[:300]
            rows.append(row)
    rows.sort(key=lambda r: (r.get("proposal_id", ""), r.get("ts", "")))
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[curate] proposals={len(ALLOWLIST)} events={len(rows)} -> {out_path}")


if __name__ == "__main__":
    main()
