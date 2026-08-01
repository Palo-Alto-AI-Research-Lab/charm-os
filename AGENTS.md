# AGENTS.md — working in this repo

Written for AI coding agents, and equally readable by a human contributor. Short on purpose.

## What this repo is

CharmOS — a framework that treats humans **and** AI agents as first-class relationships on top of a
local-first markdown vault, driven by one loop: **RDR** (Recall → Deep Research → Synthesis).

It is manifest-first: the design documents are the product, and the modules are the parts of it
that are already real. Read [`MANIFESTO.md`](MANIFESTO.md) and [`docs/architecture.md`](docs/architecture.md)
before proposing structure; a module that does not fit the RDR loop needs an argument, not a folder.

**License: Apache-2.0** (not MIT like most of this lab's repos) — check the header expectations of
any file you add.

## Stack and layout

- **Python 3, stdlib-first.** Zero-network, zero-token where the module allows it.
- `modules/eval-harness/` — the deterministic scorer. `eval.py` loads a JSONL trace, groups events
  by proposal, runs every invariant in `invariants.py`, prints a scorecard. `sanitize.py` and
  `curate_public.py` produce publishable fixtures from private traces.
- `modules/rdr/rdr.py` — the decision loop itself.
- `modules/turnstate/` — the per-turn memory ledger and its backfill.
- `docs/` — architecture, the RDR loop, privacy, and the category argument.
- `examples/` — synthetic vault and CRM entries. **Every example is fictional. Keep it that way.**

## How to verify a change

```bash
cd modules/eval-harness
python eval.py benchmarks/consensus-safety-v0/fixture.jsonl
python eval.py benchmarks/public-live-v0/fixture.jsonl --json out.json
```

**The exit code is the number of failed invariant checks** (0 = clean), so CI can gate on it — do
not "fix" a non-zero exit by changing the expectation. Same trace in, same score out: that
determinism is what makes it a benchmark rather than a demo, and it is the property to protect.

Paste the scorecard in the PR. If you added an invariant, add the fixture line that fails it.

## Conventions

- **Degrade visibly, never silently.** `load()` skips a malformed trailing line — because a live
  trace can be half-written — and *counts* it. Any new tolerance you add must be counted and
  printed the same way. A quiet skip is the bug this repo exists to catch.
- **Privacy is structural, not a review step.** Traces from a real system pass through
  `sanitize.py` before they are publishable. Never commit a fixture you have not sanitized, and
  never invent a real person's name for an example.
- Scorecards are committed as `scorecard.json` next to their fixture, so a change in scoring is
  visible as a diff.
- Docs carry the reasoning; code carries the mechanism. If a rule matters, it belongs in `docs/`
  with a pointer from the code, not duplicated in both.

## Boundaries — what needs a human

- **Adding or removing an invariant.** It changes every published score. Open an issue first.
- **Anything touching `sanitize.py`.** Weakening it can leak private data from a future trace;
  this is the one file where "it looks fine" is not review.
- **The RDR loop's shape** — the three phases and their order are the thesis of the project.
- **Relicensing or vendoring** third-party code into an Apache-2.0 repo.

## The deal

Your copyright stays yours, there is no CLA, and issues labelled `accepted` are free to take —
comment "claiming this". Full terms:
[CONTRIBUTING.md](https://github.com/Palo-Alto-AI-Research-Lab/.github/blob/main/CONTRIBUTING.md).

If an AI wrote your change, say so in the PR and confirm you ran it. Welcome here — we do it daily.
Unread generated code is the one thing that gets closed on sight.
