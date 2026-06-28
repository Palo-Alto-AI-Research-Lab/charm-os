# -*- coding: utf-8 -*-
"""
RDR -- the decision loop at the heart of CharmOS, as a tiny command-line tool.

RDR = **R**ecall  ->  **D**eep **R**esearch  ->  synthesis (a Decision Memo).
The discipline: before you act on anything strategic, first recall what you
already know, THEN research only the gaps, THEN decide -- in that order.

This module turns that loop into three deterministic commands. It has NO LLM
dependency and NO third-party packages (pure stdlib). It deliberately builds on
the module CharmOS already shipped -- the TurnState memory ledger -- so `recall`
searches your own working memory, not a black box.

    rdr recall  <query>     what do I already know? (search the TurnState ledger
                            + an optional notes directory)
    rdr research <query>    emit a structured Deep-Research prompt with the recall
                            results pre-loaded as CONTEXT, ready to paste into any
                            deep-research tool
    rdr memo    <slug>      scaffold a Decision Memo markdown file (problem ->
                            what we know -> research -> options -> decision)

WHY DETERMINISTIC RECALL
------------------------
Recall should be free and instant so you actually do it every time. The scorer
here is plain term-overlap over the ledger rows -- 0 tokens, milliseconds. It is
intentionally simple; swap in a semantic backend later without changing the loop.

CONFIG (env vars, all optional)
-------------------------------
    CHARMOS_TURNSTATE_DB   the TurnState ledger to recall from
                           (default: ~/.charmos/turnstate/turnstate.db)
    CHARMOS_NOTES_DIR      a folder of .md notes to also grep during recall
    CHARMOS_MEMO_DIR       where `rdr memo` writes (default: ./decisions)
"""
import os, sys, re, json, sqlite3, time
from collections import Counter

DEFAULT_DB = os.path.join(os.path.expanduser("~"), ".charmos", "turnstate", "turnstate.db")
STOP = set("the a an and or of to in on for is are was were be this that with from how "
           "we our you your it its they i me my should can could will would just "
           "как что это для на по из о и в с не мы наш я".split())


def db_path():
    return os.environ.get("CHARMOS_TURNSTATE_DB") or DEFAULT_DB


def terms(q):
    """Lowercased word tokens, stop-words removed. Unicode-aware (\\w covers Cyrillic)."""
    return [t for t in re.findall(r"\w+", (q or "").lower(), re.UNICODE)
            if len(t) > 1 and t not in STOP]


def score(text, qterms):
    """Rank text by WHOLE-WORD overlap with the query (not substring -- so 'art'
    does not match 'start'). Returns (#distinct terms matched, total occurrences)
    for tie-breaking. Cheap: one tokenization + a Counter."""
    if not text:
        return (0, 0)
    counts = Counter(re.findall(r"\w+", text.lower(), re.UNICODE))
    uq = qterms_unique(qterms)
    distinct = sum(1 for t in uq if counts[t])
    if not distinct:
        return (0, 0)
    total = sum(counts[t] for t in uq)
    return (distinct, total)


def qterms_unique(qterms):
    seen, out = set(), []
    for t in qterms:
        if t not in seen:
            seen.add(t); out.append(t)
    return out


def safe_decisions(raw):
    """Parse the JSON `decisions` cell defensively. Adversarial/real ledger data may
    hold a non-list (dict/string) or non-string elements; coerce to a list of str so
    callers can never crash on `dec[:120]`."""
    try:
        v = json.loads(raw or "[]")
    except Exception:
        return []
    if not isinstance(v, list):
        return []
    return [str(x) for x in v]


# ---------------------------------------------------------------- recall --------
def recall_ledger(qterms, limit=8):
    path = db_path()
    if not os.path.isfile(path):
        return []
    con = sqlite3.connect(path, timeout=5.0)
    # tolerate non-UTF8 bytes stored in TEXT columns (don't let a stray byte crash recall)
    con.text_factory = lambda b: b.decode("utf-8", "ignore") if isinstance(b, bytes) else b
    hits = []
    try:
        rows = con.execute(
            "SELECT ts, project, ask, summary, decisions FROM turns").fetchall()
    except sqlite3.OperationalError as e:
        # missing table / renamed columns -> a BROKEN integration, not "no hits".
        # Make the difference visible instead of silently returning empty.
        sys.stderr.write("rdr recall: cannot read ledger (%s) at %s\n" % (e, path))
        con.close(); return []
    except sqlite3.Error:
        con.close(); return []
    con.close()
    for ts, project, ask, summary, decisions in rows:
        blob = " ".join(x or "" for x in (ask, summary, decisions))
        d, tot = score(blob, qterms)
        if d:
            hits.append((d, tot, ts, project, ask, decisions))
    hits.sort(key=lambda h: (h[0], h[1]), reverse=True)
    return hits[:limit]


def recall_notes(qterms, limit=8):
    notes_dir = os.environ.get("CHARMOS_NOTES_DIR")
    if not notes_dir or not os.path.isdir(notes_dir):
        return []
    hits = []
    for root, _, files in os.walk(notes_dir):
        for fn in files:
            if not fn.lower().endswith((".md", ".txt")):
                continue
            fp = os.path.join(root, fn)
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                    text = fh.read()
            except OSError:
                continue
            d, tot = score(text, qterms)
            if d:
                hits.append((d, tot, fp))
    hits.sort(key=lambda h: (h[0], h[1]), reverse=True)
    return hits[:limit]


def cmd_recall(query):
    qt = terms(query)
    if not qt:
        print("recall: empty query (nothing to search for)."); return
    led = recall_ledger(qt)
    notes = recall_notes(qt)
    print("# Recall: \"%s\"" % query)
    print("\n## From the TurnState ledger (%d hit%s)"
          % (len(led), "" if len(led) == 1 else "s"))
    if not led:
        print("  (no matching turns -- this may be genuinely new territory)")
    for d, tot, ts, project, ask, decisions in led:
        print("- [%s] (%s) %s" % (ts, project or "?", (ask or "").strip()[:100]))
        for dec in safe_decisions(decisions)[:2]:
            print("    decision: %s" % dec[:120])
    if notes:
        print("\n## From notes (%s)" % os.environ.get("CHARMOS_NOTES_DIR"))
        for d, tot, fp in notes:
            print("- %s  (%d terms)" % (fp, d))
    return led, notes


# --------------------------------------------------------------- research -------
DR_TEMPLATE = """# Deep Research Prompt

## Question
{question}

## Context (auto-loaded from recall -- what we already know)
{context}

## What to find (the gaps)
- [ ] <list the specific unknowns the recall above did NOT answer>

## Deliverable
A cited report that: (1) answers the question, (2) maps the main options with
trade-offs, (3) flags risks, (4) ends with a clear recommendation + confidence
(low / medium / high). Prefer primary sources; verify contested claims.

## Constraints
Research and synthesis only -- do not take any irreversible or outward-facing
action. Surface decisions for a human to make.
"""


def cmd_research(query):
    qt = terms(query)
    led = recall_ledger(qt) if qt else []
    if led:
        ctx_lines = []
        for d, tot, ts, project, ask, decisions in led:
            ctx_lines.append("- [%s] %s" % (ts, (ask or "").strip()[:120]))
            for dec in safe_decisions(decisions)[:1]:
                ctx_lines.append("    -> %s" % dec[:120])
        context = "\n".join(ctx_lines)
    else:
        context = "  (recall found nothing relevant -- treat as a cold start)"
    print(DR_TEMPLATE.format(question=query, context=context))


# ------------------------------------------------------------------- memo -------
MEMO_TEMPLATE = """# Decision Memo -- {title}

**Date:** {date} - **Status:** draft - **Protocol:** RDR

## Problem / question
<one paragraph: what are we deciding and why now?>

## What we already know (recall)
<paste `rdr recall "{title}"` output; we are not starting cold>

## Deep research findings
<paste the synthesized report from `rdr research "{title}"`>

## Options
1. **<option A>** - pros / cons
2. **<option B>** - pros / cons

## Risks
- 🔴 <blocking risk> -> mitigation
- 🟡 <secondary risk> -> mitigation

## Decision
<the call + confidence (low/med/high). What we will do, and what we explicitly will NOT do.>

## Next
- [ ] <first concrete step, with owner>
"""


def slugify(s):
    s = re.sub(r"[^\w\- ]+", "", (s or "").strip().lower(), flags=re.UNICODE)
    return re.sub(r"[\s_]+", "-", s)[:60] or "decision"


def cmd_memo(title):
    memo_dir = os.environ.get("CHARMOS_MEMO_DIR") or os.path.join(os.getcwd(), "decisions")
    os.makedirs(memo_dir, exist_ok=True)
    path = os.path.join(memo_dir, "decision-%s.md" % slugify(title))
    if os.path.exists(path):
        print("memo: already exists, not overwriting -> %s" % path); return
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(MEMO_TEMPLATE.format(title=title, date=time.strftime("%Y-%m-%d")))
    print("memo scaffolded -> %s" % path)


USAGE = "usage: rdr {recall|research|memo} <query-or-title>"


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(USAGE); return 0
    cmd = argv[1]
    arg = " ".join(argv[2:]).strip()
    if cmd in ("recall", "research", "memo") and not arg:
        print("%s: missing argument\n%s" % (cmd, USAGE)); return 2
    if cmd == "recall":
        cmd_recall(arg)
    elif cmd == "research":
        cmd_research(arg)
    elif cmd == "memo":
        cmd_memo(arg)
    else:
        print(USAGE); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
