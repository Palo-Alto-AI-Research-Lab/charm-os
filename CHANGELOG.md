# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `modules/eval-harness/` (v0.1.0) — eval & trace harness for multi-agent fleets. Four deterministic
  behavioural invariants (human gate before risky commit, independent verify before commit, no
  duplicate-event storms, escalations resolved), a zero-token evaluator whose exit code is the number
  of failed checks, a provider-neutral JSONL trace schema, and two benchmarks built from six weeks of
  our own production fleet: a readable showcase (`public-live-v0`) and the full 317-event corpus
  (`consensus-safety-v0`). Published results include our own failure: independent verify at 7.7%.
  Sanitisation ships as two deterministic paths (structure-only whitelist, and allowlist curation
  keeping real text); the host role map is local config, never source.

### Planned
- Second Brain reference implementation (vault + RAG + reranker).
- Graph / associative recall layer with entity-vs-theme gating.
- C(H+A)RM relationship layer (humans + agents as contacts).
- Import pipelines and skills library.

## [0.3.0] - 2026-06-28

### Added
- **Module `modules/rdr/`** — the RDR loop as a CLI: `recall` (whole-word search
  over the TurnState ledger + optional notes dir), `research` (emits a Deep-Research
  prompt with recall pre-loaded as context), `memo` (scaffolds a Decision Memo).
  Pure stdlib, zero LLM tokens; builds directly on the TurnState module.
- Module passed an independent adversarial review before publishing; defensive
  parsing of ledger cells, schema-mismatch warning, non-UTF8 tolerance.

## [0.2.0] - 2026-06-28

### Added
- **First runnable module: `modules/turnstate/`** — the always-on memory ledger.
  Per-turn deterministic working-state row written to SQLite, **zero LLM tokens**,
  pure stdlib. Two halves: `turnstate_hook.py` (real-time `Stop`-hook fast path) and
  `turnstate_backfill.py` (idempotent rebuild straight from transcripts + a
  `--check` freshness gate, so the ledger can never silently rot).
- Module `README.md` documenting design, integration, and config.

## [0.1.0] - 2026-06-27

### Added
- Manifest-first V1: vision, architecture overview, and documentation.
- `README.md`, `MANIFESTO.md`.
- `/docs`: architecture, RDR loop, C(H+A)RM category, privacy.
- `/examples`: synthetic-only sample vault and contacts.
- `LICENSE` (Apache-2.0), `.env.example`.

[Unreleased]: https://github.com/Palo-Alto-AI-Research-Lab/charm-os
[0.3.0]: https://github.com/Palo-Alto-AI-Research-Lab/charm-os/releases/tag/v0.3.0
[0.2.0]: https://github.com/Palo-Alto-AI-Research-Lab/charm-os/releases/tag/v0.2.0
[0.1.0]: https://github.com/Palo-Alto-AI-Research-Lab/charm-os/releases/tag/v0.1.0
