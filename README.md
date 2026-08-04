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
- [`modules/eval-harness/`](modules/eval-harness/) (v0.1.0) — **grade your agent fleet against rules it must never break.** Turns a multi-agent event log into reproducible traces and scores them against explicit safety invariants. Includes our own production results: human-gate before a risky commit **100%**, independent verify before commit **7.7%** — we publish both.

All deterministic, zero-LLM-token, pure stdlib. More modules follow.

### Roadmap

**Now — [v0.4.0](https://github.com/Palo-Alto-AI-Research-Lab/charm-os/releases).** The three
modules above, each versioned on its own, plus the manifesto and docs that came first.

**Next**, from [CHANGELOG.md](CHANGELOG.md): a Second Brain reference implementation (vault + RAG +
reranker), the graph/associative recall layer with entity-vs-theme gating, the C(H+A)RM relationship
layer (humans and agents as contacts), and the import pipelines.

We version with [SemVer](https://semver.org), and **every noticeable change ships as a new release**
— a shipped module is a release, cut when the work lands rather than when someone remembers. The
[release feed](https://github.com/Palo-Alto-AI-Research-Lab/charm-os/releases) is how you tell what
is real here from what is still a manifesto.

## Privacy (read this first)

This framework operates on deeply personal data. **No real personal data is included in this repository.** Everything under [`/examples`](examples/) is synthetic. If you self-host, your data stays yours and local. See [docs/privacy.md](docs/privacy.md).

## Cite this work

If this repo shows up in your research, cite it via [CITATION.cff](CITATION.cff) (GitHub's "Cite this repository" button). Author: **Anton Dziatkovskii** ([ORCID 0000-0001-7408-3054](https://orcid.org/0000-0001-7408-3054), GitHub [@antondz](https://github.com/antondz)) — one spelling everywhere, in publications, commits and `CITATION.cff`.

## AI contributors

This project is built by a human + AI team, and the git log says so: Claude
writes most of the code, Codex and Grok review it, Gemini feeds the research.
Each is credited on a commit **only if its output changed that commit's
content** — no decorative credits. Lab-wide policy, one source for every repo:
[AI-CONTRIBUTORS.md](https://github.com/Palo-Alto-AI-Research-Lab/.github/blob/main/AI-CONTRIBUTORS.md).

## License

[Apache License 2.0](LICENSE). Permissive, with an explicit patent grant. An open-core path (optional paid layer/hosting) may follow, but the core stays open.

---

Built by [Palo Alto AI Research Lab](https://github.com/Palo-Alto-AI-Research-Lab). Contributions and discussion welcome once V1 docs settle.

## Contact

Questions, war stories, or you want to run this on your own fleet:

- 💬 WhatsApp: **+1 341 222 9178**
- 🐦 X: [@Tony_Stef_](https://x.com/Tony_Stef_)
- 📣 Telegram: [@ClawRus](https://t.me/ClawRus) (RU) · [@ClawEng](https://t.me/ClawEng) (EN)
- 🌐 [palo-alto.ai](https://palo-alto.ai) · [Palo Alto AI Research Lab](https://github.com/Palo-Alto-AI-Research-Lab)
