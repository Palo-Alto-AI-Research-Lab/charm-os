# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Second Brain reference implementation (vault + RAG + reranker).
- Graph / associative recall layer with entity-vs-theme gating.
- C(H+A)RM relationship layer (humans + agents as contacts).
- RDR loop tooling (Recall to Deep Research to Decision Memo).
- Import pipelines and skills library.

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
[0.2.0]: https://github.com/Palo-Alto-AI-Research-Lab/charm-os/releases/tag/v0.2.0
[0.1.0]: https://github.com/Palo-Alto-AI-Research-Lab/charm-os/releases/tag/v0.1.0
