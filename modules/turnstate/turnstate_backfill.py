# -*- coding: utf-8 -*-
"""
TurnState BACKFILL + FRESHNESS GATE -- the self-healing half of the memory ledger.

WHY THIS EXISTS
---------------
The `Stop`-hook fast path (turnstate_hook.py) depends on a single trigger firing on
EVERY turn of EVERY session. That trigger fails silently when a session predates the
hook's registration, when the harness requires re-approval after a config edit, or on
any harness change -- and because the hook swallows errors, the failure is INVISIBLE:
the ledger looks alive while recording nothing.

THE FIX (closes the whole class of failure)
-------------------------------------------
The raw session transcripts are the immutable source of truth. This script
reconstructs the ledger DIRECTLY from them, so the box is correct whether or not the
hook ever fired. It is idempotent: it only ingests transcript bytes BEYOND what is
already recorded per session (a per-session high-water mark), so re-running is safe
and cheap. Run it on a schedule (e.g. nightly) and the ledger can never silently rot.

USAGE
-----
    python turnstate_backfill.py            # ingest all new turns from all transcripts
    python turnstate_backfill.py --check    # FRESHNESS GATE: exit 2 if the box is stale
    python turnstate_backfill.py --stats    # row / session counts

CONFIG (env vars, all optional)
-------------------------------
    CHARMOS_TURNSTATE_DB     SQLite path (shared with turnstate_hook.py)
    CHARMOS_TRANSCRIPTS_GLOB glob for session transcripts
                             (default: ~/.claude/projects/*/*.jsonl  -- Claude Code)

Pure stdlib. Reuses turnstate_hook.py's parsers so backfill rows == hook rows.
"""
import os, sys, json, glob, time, sqlite3, importlib.util
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "turnstate_hook.py")
TRANSCRIPTS_GLOB = os.environ.get(
    "CHARMOS_TRANSCRIPTS_GLOB",
    os.path.join(os.path.expanduser("~"), ".claude", "projects", "*", "*.jsonl"))

# reuse the hook's parsing so a backfilled row is identical to a live-captured one
_spec = importlib.util.spec_from_file_location("turnstate_hook", HOOK)
_h = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_h)

CLIP_ASK, CLIP_SUMMARY, CLIP_CMD = _h.CLIP_ASK, _h.CLIP_SUMMARY, _h.CLIP_CMD
FILE_TOOLS, DECISION_RX, uniq = _h.FILE_TOOLS, _h.DECISION_RX, _h.uniq


def iso_to_local(s):
    """'2026-06-26T18:41:24.348Z' -> local '2026-06-26 18:41:24'. Fallback: now."""
    if not s:
        return time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).astimezone() \
            .strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return time.strftime("%Y-%m-%d %H:%M:%S")


def build_row(sid, cwd, ask, asm_parts, files, tools, commands, b0, b1, ts=None):
    summary = "\n".join(asm_parts).strip()
    decisions = []
    for ln in summary.splitlines():
        ln = ln.strip(" -*#>").strip()
        if 8 <= len(ln) <= 180 and DECISION_RX.search(ln):
            decisions.append(ln)
    if not (ask or summary or files or commands):
        return None
    return (
        sid, iso_to_local(ts), cwd,
        os.path.basename(cwd.rstrip("\\/")) if cwd else "",
        ask[:CLIP_ASK], summary[:CLIP_SUMMARY],
        json.dumps(uniq(files), ensure_ascii=False),
        json.dumps(uniq(tools), ensure_ascii=False),
        json.dumps(commands[:20], ensure_ascii=False),
        json.dumps(uniq(decisions)[:10], ensure_ascii=False),
        "(backfill)", b0, b1,
    )


def segment_tail(raw_bytes, start_off):
    """Split an unprocessed transcript tail into per-turn segments.
    A turn boundary = a real user-text message. Tracks byte spans for idempotency."""
    turns, cur, off = [], None, start_off
    for line in raw_bytes.splitlines(keepends=True):
        line_off = off
        off += len(line)
        s = line.strip()
        if not s:
            continue
        try:
            ev = json.loads(s.decode("utf-8", "ignore"))
        except Exception:
            continue
        t = ev.get("type")
        evts = ev.get("timestamp")
        if t == "user":
            txt = _h.text_of(ev)
            if _h.is_real_user_text(txt):
                if cur and (cur["ask"] or cur["asm"] or cur["files"] or cur["cmd"]):
                    cur["b1"] = line_off
                    turns.append(cur)
                cur = {"ask": txt, "asm": [], "files": [], "tools": [],
                       "cmd": [], "b0": line_off, "b1": off, "ts": evts}
        elif t == "assistant":
            if cur is None:
                cur = {"ask": "", "asm": [], "files": [], "tools": [],
                       "cmd": [], "b0": line_off, "b1": off, "ts": evts}
            txt = _h.text_of(ev)
            if evts:
                cur["ts"] = evts
            if txt:
                cur["asm"].append(txt)
            for name, inp in _h.tool_uses(ev):
                if name:
                    cur["tools"].append(name)
                if name in FILE_TOOLS:
                    fp = inp.get("file_path") or inp.get("notebook_path")
                    if fp:
                        cur["files"].append(fp)
                if name == "Bash":
                    c = (inp.get("command") or "").strip()
                    if c:
                        cur["cmd"].append(c[:CLIP_CMD])
            cur["b1"] = off
    if cur and (cur["ask"] or cur["asm"] or cur["files"] or cur["cmd"]):
        turns.append(cur)
    return turns


def cwd_of(tpath):
    """Best-effort cwd from the first event that carries one."""
    try:
        with open(tpath, "r", encoding="utf-8", errors="ignore") as fh:
            for _ in range(50):
                line = fh.readline()
                if not line:
                    break
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if ev.get("cwd"):
                    return ev["cwd"]
    except Exception:
        pass
    return ""


def ensure_coverage(con):
    con.execute("""CREATE TABLE IF NOT EXISTS coverage(
        session_id TEXT PRIMARY KEY, scanned_end INTEGER, ts TEXT)""")
    con.commit()


def covered_end(con, sid):
    """High-water mark = max(recorded row byte_end, scanned coverage)."""
    a = con.execute("SELECT MAX(byte_end) FROM turns WHERE session_id=?", (sid,)).fetchone()
    b = con.execute("SELECT scanned_end FROM coverage WHERE session_id=?", (sid,)).fetchone()
    return max(int(a[0]) if a and a[0] else 0, int(b[0]) if b and b[0] else 0)


def backfill(con):
    _h.ensure_db(con)
    ensure_coverage(con)
    added = files_seen = 0
    for tpath in glob.glob(TRANSCRIPTS_GLOB):
        sid = os.path.splitext(os.path.basename(tpath))[0]
        files_seen += 1
        try:
            fsize = os.path.getsize(tpath)
        except OSError:
            continue
        start = covered_end(con, sid)
        if start >= fsize:
            continue
        with open(tpath, "rb") as fh:
            fh.seek(start)
            raw = fh.read()
        cwd = cwd_of(tpath)
        for seg in segment_tail(raw, start):
            r = build_row(sid, cwd, seg["ask"], seg["asm"], seg["files"],
                          seg["tools"], seg["cmd"], seg["b0"], seg["b1"], seg.get("ts"))
            if r:
                con.execute(
                    "INSERT INTO turns(session_id,ts,cwd,project,ask,summary,files,"
                    "tools,commands,decisions,evidence,byte_start,byte_end) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", r)
                added += 1
        # mark this file SCANNED to EOF even if its tail produced no row (pure
        # tool-result tails) -> prevents the freshness gate from false-positiving.
        con.execute("INSERT INTO coverage(session_id,scanned_end,ts) VALUES(?,?,?) "
                    "ON CONFLICT(session_id) DO UPDATE SET scanned_end=excluded.scanned_end,"
                    "ts=excluded.ts", (sid, fsize, time.strftime("%Y-%m-%d %H:%M:%S")))
        con.commit()
    return added, files_seen


def check_freshness(con):
    """GATE: exit 2 if a FINISHED session (not modified in the last hour) still has
    >4KB of un-ingested transcript. Active sessions are skipped (a live session
    always has a tail until it stops -> not a real miss)."""
    _h.ensure_db(con)
    ensure_coverage(con)
    total = con.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
    uncovered, now = 0, time.time()
    for tpath in glob.glob(TRANSCRIPTS_GLOB):
        sid = os.path.splitext(os.path.basename(tpath))[0]
        try:
            fsize = os.path.getsize(tpath)
            if now - os.path.getmtime(tpath) < 3600:   # active session, skip
                continue
        except OSError:
            continue
        if fsize - covered_end(con, sid) > 4096:
            uncovered += 1
    print("TurnState rows: %d | finished sessions with un-ingested turns: %d"
          % (total, uncovered))
    if uncovered:
        print("STALE: run backfill.")
        return 2
    print("FRESH: ledger covers all transcript activity.")
    return 0


def stats(con):
    _h.ensure_db(con)
    tot = con.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
    sess = con.execute("SELECT COUNT(DISTINCT session_id) FROM turns").fetchone()[0]
    print("total turns: %d across %d sessions" % (tot, sess))
    for d, c in con.execute("SELECT substr(ts,1,10) d, COUNT(*) FROM turns "
                            "GROUP BY d ORDER BY d DESC LIMIT 14"):
        print("  %s : %d" % (d, c))


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    con = sqlite3.connect(db_path_shared(), timeout=10.0)
    try:
        if arg == "--check":
            sys.exit(check_freshness(con))
        if arg == "--stats":
            stats(con); return
        added, files_seen = backfill(con)
        print("backfill: scanned %d transcripts, added %d turns" % (files_seen, added))
        stats(con)
    finally:
        con.close()


def db_path_shared():
    # use the exact same resolution as the hook so both write one ledger
    return _h.db_path()


if __name__ == "__main__":
    main()
