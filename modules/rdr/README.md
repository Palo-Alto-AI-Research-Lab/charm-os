# RDR — the decision loop, as a CLI

> **RDR = Recall → Deep Research → synthesis.** The spine of CharmOS: before you
> act on anything strategic, recall what you already know, research only the gaps,
> then decide — in that order.

This module turns that loop into three deterministic commands. **No LLM, no
third-party packages** (pure stdlib). It builds on the module CharmOS already
shipped — the [TurnState](../turnstate/) memory ledger — so `recall` searches your
own working memory, not a black box.

## Commands

```bash
# 1. RECALL — what do I already know?
#    Searches the TurnState ledger (+ an optional notes dir) by term overlap.
python rdr.py recall "agent memory architecture"

# 2. RESEARCH — emit a Deep-Research prompt with recall pre-loaded as CONTEXT.
#    Paste the output into any deep-research tool.
python rdr.py research "should we adopt an open-core license"

# 3. MEMO — scaffold a Decision Memo to synthesize into.
python rdr.py memo "open-core license"
```

## Why deterministic recall

Recall must be free and effectively instant, or you won't do it every time. The
scorer is plain whole-word term-overlap over the ledger rows — zero tokens and
Unicode-aware (works across languages). It is a linear scan of the `turns` table,
which is fast for typical ledgers; for very large ledgers swap in an FTS or semantic
backend behind the same loop without changing how you work.

## The loop in practice

1. `rdr recall "<question>"` — see what past sessions already decided. Often you
   find you've half-solved this before.
2. `rdr research "<question>"` — the gaps that recall did **not** answer become the
   Deep-Research prompt (recall results are injected as CONTEXT so the research
   doesn't repeat what you know).
3. `rdr memo "<question>"` — scaffold a Decision Memo; paste recall + research into
   it, fill Options / Risks / Decision, and only then act.

## Config (env vars, all optional)

| var | default | purpose |
|---|---|---|
| `CHARMOS_TURNSTATE_DB` | `~/.charmos/turnstate/turnstate.db` | ledger to recall from |
| `CHARMOS_NOTES_DIR` | _(unset)_ | extra folder of `.md`/`.txt` notes to grep in recall |
| `CHARMOS_MEMO_DIR` | `./decisions` | where `rdr memo` writes |

## Design notes

- **Recall before research before decision** is the whole point. The tool nudges
  you through the order so you stop jumping straight to action on a cold opinion.
- **Local-only.** It reads your ledger/notes and writes a memo file; nothing leaves
  your machine. The `research` command only *emits a prompt* — running it is your
  call, in whatever tool you choose.
- **It writes where you point it.** `rdr memo` creates files under `CHARMOS_MEMO_DIR`
  (default `./decisions`); `recall` recursively reads every `.md`/`.txt` under
  `CHARMOS_NOTES_DIR` if set. Point these at directories you intend — the tool does
  not sandbox them. It never overwrites an existing memo.
