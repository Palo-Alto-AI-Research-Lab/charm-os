# -*- coding: utf-8 -*-
"""
TurnState -- a per-turn semantic-state ledger for an AI coding/agent session.

This is the first runnable module of CharmOS: the "always-on memory" pillar from
the manifesto, in its cheapest, most honest form.

WHAT IT DOES
------------
After EVERY assistant turn, an agent harness can call this script as a `Stop` hook.
It parses only the NEW tail of the session transcript and writes ONE deterministic
row to a SQLite ledger describing what just happened:

    ask | summary | files-touched | tools-used | shell-commands | decision-lines | evidence-pointer

The point: the raw transcript stays the immutable source of truth, and this is the
cheap DERIVED working-state you actually recall against later. **Zero LLM tokens** --
everything is extracted by plain parsing (sqlite3 + json + re, pure stdlib).

WHY DETERMINISTIC (no LLM here)
-------------------------------
Recall is a high-frequency operation; paying an LLM on every turn to summarize is
wasteful and adds latency + a failure mode. A deterministic delta is free, instant,
and good enough to reconstruct "where were we". An optional LLM enrichment pass can
run later, offline, over the cheap rows -- not on the hot path.

INTEGRATION (Claude Code example)
---------------------------------
Register as a `Stop` hook. The harness pipes a JSON event on stdin containing at
least `session_id` and `transcript_path`. This script never prints to stdout and
never raises into the session: ANY error -> exit 0. A silent failure mode, though,
is dangerous (the ledger looks alive while capturing nothing) -- so this module
ships WITH `turnstate_backfill.py`, which reconstructs the ledger directly from
transcripts on a schedule. Belt and suspenders: the hook is the fast path, the
backfill is the guarantee.

CONFIG (env vars, all optional)
-------------------------------
    CHARMOS_TURNSTATE_DB   full path to the SQLite file
                           (default: ~/.charmos/turnstate/turnstate.db)
"""
import sys, os, json, re, sqlite3, tempfile, time


# --- where the ledger lives ----------------------------------------------------
def db_path():
    env = os.environ.get("CHARMOS_TURNSTATE_DB")
    if env:
        try:
            os.makedirs(os.path.dirname(env), exist_ok=True)
            return env
        except Exception:
            pass
    base = os.path.join(os.path.expanduser("~"), ".charmos", "turnstate")
    try:
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, "turnstate.db")
    except Exception:
        return os.path.join(tempfile.gettempdir(), "turnstate.db")


CLIP_ASK = 500
CLIP_SUMMARY = 1200
CLIP_CMD = 200
MAX_NEW_BYTES = 4 * 1024 * 1024   # don't read more than 4MB of new tail in one turn

# Lines that look like a decision / next-step / TODO are flagged. Customize freely;
# the set below is intentionally multilingual because real sessions are.
DECISION_RX = re.compile(
    r"(\bdecid(?:e|ed|sion)\b|we (?:will|should|chose|picked)|\btodo\b|to-?do|"
    r"next step|\bverdict\b|\bchose\b|\bpicked\b|"
    r"реш(?:ил|ено|аем)|дел(?:аем|ать)\b|вердикт|следующий шаг|рекомендаци)",
    re.IGNORECASE)

FILE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def text_of(ev):
    """Flatten an event's message content (string or block-list) to plain text."""
    msg = ev.get("message") or {}
    c = msg.get("content")
    if isinstance(c, str):
        return c.strip()
    if isinstance(c, list):
        out = []
        for b in c:
            if isinstance(b, dict) and b.get("type") == "text":
                out.append(b.get("text") or "")
        return " ".join(p.strip() for p in out if p).strip()
    return ""


def is_real_user_text(t):
    """Filter out harness noise (system reminders, slash-command echoes, caveats)."""
    if not t or len(t) < 3:
        return False
    head = t.lstrip()[:40].lower()
    if head.startswith("<") or "system-reminder" in head or "<command-" in head:
        return False
    if "caveat:" in head or "local-command" in head:
        return False
    return True


def tool_uses(ev):
    """Yield (name, input_dict) for tool_use blocks in an assistant event."""
    msg = ev.get("message") or {}
    c = msg.get("content")
    if isinstance(c, list):
        for b in c:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                yield (b.get("name") or "", b.get("input") or {})


# --- per-session byte offset so each turn reads only NEW transcript lines -------
def offset_file(sid):
    sid = "".join(ch for ch in str(sid or "unknown") if ch.isalnum() or ch in "-_")[:80]
    return os.path.join(tempfile.gettempdir(), "charmos-turnstate-%s.off" % (sid or "unknown"))


def read_offset(sid, fsize):
    try:
        with open(offset_file(sid), "r") as f:
            off = int(f.read().strip())
        if 0 <= off <= fsize:
            return off
    except Exception:
        pass
    return 0


def write_offset(sid, off):
    try:
        with open(offset_file(sid), "w") as f:
            f.write(str(off))
    except Exception:
        pass


def ensure_db(con):
    con.execute("""CREATE TABLE IF NOT EXISTS turns(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT, ts TEXT, cwd TEXT, project TEXT,
        ask TEXT, summary TEXT,
        files TEXT, tools TEXT, commands TEXT, decisions TEXT,
        evidence TEXT, byte_start INTEGER, byte_end INTEGER
    )""")
    con.execute("CREATE INDEX IF NOT EXISTS ix_turns_sid ON turns(session_id)")
    con.commit()


def uniq(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x); out.append(x)
    return out


def main():
    data = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace"))

    sid = str(data.get("session_id") or "")
    tpath = data.get("transcript_path") or ""
    cwd = data.get("cwd") or ""

    if not tpath or not os.path.isfile(tpath):
        return

    fsize = os.path.getsize(tpath)
    start = read_offset(sid, fsize)
    if fsize - start > MAX_NEW_BYTES:   # huge gap (e.g. first turn of a resumed session)
        write_offset(sid, fsize)        # -> let the backfill handle it, just advance
        return
    if fsize <= start:                  # nothing new
        return

    with open(tpath, "r", encoding="utf-8", errors="ignore") as fh:
        fh.seek(start)
        chunk = fh.read()
    write_offset(sid, fsize)            # advance regardless, never re-process

    ask = ""
    files, tools, commands, summary_parts = [], [], [], []
    for line in chunk.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        t = ev.get("type")
        if t == "user":
            txt = text_of(ev)
            if is_real_user_text(txt):
                ask = txt              # last real user msg in this slice = the turn's ask
        elif t == "assistant":
            txt = text_of(ev)
            if txt:
                summary_parts.append(txt)
            for name, inp in tool_uses(ev):
                if name:
                    tools.append(name)
                if name in FILE_TOOLS:
                    fp = inp.get("file_path") or inp.get("notebook_path")
                    if fp:
                        files.append(fp)
                if name == "Bash":
                    cmd = (inp.get("command") or "").strip()
                    if cmd:
                        commands.append(cmd[:CLIP_CMD])

    summary = "\n".join(summary_parts).strip()
    decisions = []
    for ln in summary.splitlines():
        ln = ln.strip(" -*#>").strip()
        if 8 <= len(ln) <= 180 and DECISION_RX.search(ln):
            decisions.append(ln)

    # nothing meaningful happened (e.g. a pure tool-result turn) -> skip writing noise
    if not (ask or summary or files or commands):
        return

    row = (
        sid, time.strftime("%Y-%m-%d %H:%M:%S"), cwd,
        os.path.basename(cwd.rstrip("\\/")) if cwd else "",
        ask[:CLIP_ASK], summary[:CLIP_SUMMARY],
        json.dumps(uniq(files), ensure_ascii=False),
        json.dumps(uniq(tools), ensure_ascii=False),
        json.dumps(commands[:20], ensure_ascii=False),
        json.dumps(uniq(decisions)[:10], ensure_ascii=False),
        tpath, start, fsize,
    )
    con = sqlite3.connect(db_path(), timeout=3.0)
    try:
        ensure_db(con)
        con.execute(
            "INSERT INTO turns(session_id,ts,cwd,project,ask,summary,files,tools,"
            "commands,decisions,evidence,byte_start,byte_end) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", row)
        con.commit()
    finally:
        con.close()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass   # never break a session
    sys.exit(0)
