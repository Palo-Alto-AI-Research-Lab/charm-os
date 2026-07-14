# CharmOS · {C(H+A)RM}

**The first open-source framework that manages both your human contacts AND your AI agents as first-class relationships, on top of a personal "second brain", driven by one decision loop: RDR.**

> C(H+A)RM = **C**RM for **H**umans **+ A**gents **R**elationship **M**anagement.
> RDR = **R**ecall to **D**eep **R**esearch to synthesis. The loop that turns memory into decisions.

---

## What this is

Three things most people keep in separate silos, unified into one open framework:

1. **Second Brain** to a private, local-first knowledge base (markdown vault) with semantic recall (embeddings + reranker), an always-on per-turn memory ledger, and a graph/associative recall layer.
2. **C(H+A)RM** to a relationship layer that treats **people and AI agents alike** as contacts you maintain: notes, history, warm intros, follow-ups.
3. **RDR** to the method that ties them together: **Recall** what you already know, run **Deep Research** to fill the gaps, then **synthesize** into a Decision Memo before you act.

## Why it is different

The ecosystem is rich but siloed:

| Space | Examples | What they miss |
|---|---|---|
| Personal knowledge (PKM) | AFFiNE, Logseq, Khoj, Quivr | no agent memory, no contacts |
| Agent / LLM memory | Mem0, Letta, Cognee, Graphiti | no personal vault, no human CRM |
| Personal CRM | Monica, Twenty | ignore AI agents entirely |

**No tool spans personal notes to agent memory to human CRM, and none prescribe a structured decision loop.** That intersection, plus RDR, is the whole point.

## Who it is for

Founders, researchers, and operators who want a durable "digital twin" of how they think and who they know, that they fully own, can repair themselves, and can grow over years.

## Architecture (high level)

```
        ┌──────────────────────────────────────────────┐
        │                   RDR LOOP                     │
        │  Recall  ->  Deep Research  ->  Synthesis      │
        └───────▲───────────────────────────────┬───────┘
                │                                 │
        ┌───────┴────────┐               ┌────────▼────────┐
        │  SECOND BRAIN  │               │    C(H+A)RM     │
        │ vault + RAG +  │◄─────────────►│ humans + agents │
        │ memory ledger  │   shared      │ as contacts     │
        │ + graph recall │   knowledge   │ intros, history │
        └───────▲────────┘               └────────▲────────┘
                │                                 │
        ┌───────┴─────────────────────────────────┴───────┐
        │   Import pipelines (chat / mail / calls / docs)   │
        │   Skills (composable agent commands)             │
        └──────────────────────────────────────────────────┘
```

## Status

**Manifest-first, now with runnable modules.** This repository shipped the **vision, architecture, and docs** first (see [MANIFESTO.md](MANIFESTO.md) and [`/docs`](docs/)); real code is now landing under [`modules/`](modules/):

- [`modules/turnstate/`](modules/turnstate/) (v0.2.0) — the **always-on memory ledger**: per-turn deterministic working state, hook + self-healing backfill.
- [`modules/rdr/`](modules/rdr/) (v0.3.0) — the **RDR loop** as a CLI: `recall` → `research` → `memo`, built on the TurnState ledger.

All deterministic, zero-LLM-token, pure stdlib. More modules follow. We version with [SemVer](https://semver.org) and keep a [CHANGELOG](CHANGELOG.md).

## Privacy (read this first)

This framework operates on deeply personal data. **No real personal data is included in this repository.** Everything under [`/examples`](examples/) is synthetic. If you self-host, your data stays yours and local. See [docs/privacy.md](docs/privacy.md).

## Cite this work

If this repo shows up in your research, cite it via [CITATION.cff](CITATION.cff) (GitHub's "Cite this repository" button). Academic identity: Anton Dzyatkovsky publishes as **Anton Dziatkovskii** ([ORCID 0000-0001-7408-3054](https://orcid.org/0000-0001-7408-3054)).

## License

[Apache License 2.0](LICENSE). Permissive, with an explicit patent grant. An open-core path (optional paid layer/hosting) may follow, but the core stays open.

---

Built by [Palo Alto AI Research Lab](https://github.com/Palo-Alto-AI-Research-Lab). Contributions and discussion welcome once V1 docs settle.
