# TurnState — always-on memory ledger

> The first runnable CharmOS module: the **always-on memory** pillar from the
> [manifesto](../../MANIFESTO.md), in its cheapest honest form.

TurnState gives an AI coding/agent session a **durable, queryable working memory** —
without spending a single LLM token to maintain it.

## The idea

The raw session transcript (`.jsonl`) is the immutable source of truth, but it is
huge and slow to recall against. TurnState writes, after each turn, one small
**deterministic** row capturing what just happened:

| column | meaning |
|---|---|
| `ask` | the user's request this turn |
| `summary` | the assistant's response text |
| `files` | files written/edited |
| `tools` | tools invoked |
| `commands` | shell commands run |
| `decisions` | lines that look like a decision / next-step / TODO |
| `evidence` | pointer back to the raw transcript |

That cheap derived layer is what you recall against to answer *"where were we?"*.

## Two halves: fast path + guarantee

Relying only on a per-turn hook is fragile — if the hook is unregistered, predates
the session, or the harness changes, it fails **silently** and the ledger looks
alive while capturing nothing. So TurnState ships two pieces:

- **`turnstate_hook.py`** — the real-time fast path. Register it as a `Stop` hook;
  it appends one row per turn, reading only the new transcript tail. Zero tokens,
  pure stdlib, never raises into the session.
- **`turnstate_backfill.py`** — the guarantee. It reconstructs the ledger directly
  from transcripts, idempotently (per-session byte high-water mark), so the box is
  correct *whether or not the hook fired*. Run it on a schedule. `--check` is a
  freshness gate that exits non-zero if a finished session has missed turns.

Belt and suspenders: the hook keeps memory live; the backfill keeps it honest.

## Quick start

```bash
# one-off rebuild from all transcripts (safe to re-run; idempotent)
python turnstate_backfill.py

# freshness gate (exit 2 if stale) — wire into a nightly job
python turnstate_backfill.py --check

# counts
python turnstate_backfill.py --stats
```

Register the hook with your harness (Claude Code example — a `Stop` hook that pipes
the session event JSON to the script on stdin). The harness provides `session_id`
and `transcript_path`; the script writes only to SQLite.

## Config (env vars, all optional)

| var | default | purpose |
|---|---|---|
| `CHARMOS_TURNSTATE_DB` | `~/.charmos/turnstate/turnstate.db` | ledger location |
| `CHARMOS_TRANSCRIPTS_GLOB` | `~/.claude/projects/*/*.jsonl` | where backfill finds transcripts |

## Design notes

- **Deterministic, not LLM.** Recall is high-frequency; summarizing with an LLM on
  every turn is wasteful and adds a failure mode. An optional enrichment pass can run
  later, offline, over these cheap rows — never on the hot path.
- **The transcript stays canonical.** TurnState is a derived index you can delete and
  rebuild at any time from `turnstate_backfill.py`.
- **Privacy.** The ledger is local. It contains your own session content; treat it as
  you would the transcripts themselves. Nothing is sent anywhere.
