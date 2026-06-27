# Architecture

Three layers plus the loop that drives them.

## 1. Second Brain (knowledge + memory)

- **Vault:** local-first markdown notes. Plain files, no lock-in.
- **Semantic recall:** embeddings (e5-class) + a reranker over a curated layer, so retrieval returns the smallest relevant slice instead of dumping the corpus.
- **Memory ledger:** an always-on, per-turn record of work (what was asked, files touched, decisions). Deterministic, near-zero token cost, survives crashes.
- **Associative recall:** a graph-expansion layer over outgoing links. Gated by query type: themes get graph expansion, entity/name lookups stay pure-vector (graph hurts precise-name queries).

## 2. C(H+A)RM (relationships)

- **Unified contact model:** a human and an AI agent share the same primitives (profile, history, notes, follow-ups).
- **Funnel:** warm intros, status tracking, next-action with owner and due date.
- **Grounded in the vault:** every contact links back into the knowledge layer.

## 3. Pipelines and skills

- **Import pipelines:** bring chats, mail, call transcripts, and docs into the vault, idempotently and deterministically.
- **Skills:** composable agent commands. Thin orchestrators over deterministic helpers, read-only first.

## The RDR loop (cross-cutting)

```
Recall  ->  Deep Research  ->  Synthesis  ->  Decision Memo  ->  act
   ^                                                            |
   └──────────────── new knowledge folds back in ──────────────┘
```

See [rdr-loop.md](rdr-loop.md).

## Design constraints

- **Local-first, you own the data.**
- **Repairable by a non-engineer.** Prefer the simplest thing that works; flag and justify any added complexity.
- **Cheap tool first.** Answer with SQL / grep / retrieval before calling an LLM; the model only gets the remaining slice.
- **Code out, data home.** The framework is open; personal data never is.
