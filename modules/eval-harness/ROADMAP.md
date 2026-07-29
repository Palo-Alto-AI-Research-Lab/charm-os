# Roadmap - tracekit

Falsifiable milestones only. Each has a written acceptance bar so "done" is measurable, not vibes  - 
the same discipline the harness enforces on the fleet.

## v0 - DESIGN DRAFT (this session) ✅
- Trace schema, 4 invariants, deterministic eval, TWO real benchmarks:
  `public-live-v0` (readable showcase, real subjects) + `consensus-safety-v0` (full structural corpus).
- **Bar met:** both fixtures reproduce byte-for-byte; the live Tier-2 trace reads end-to-end and its
  scorecard shows INV-1 ✅ / INV-2 ✗ in one example.

## v1 - PUBLIC MODULE (blocked on monorepo publication forks)
Single-model, done impeccably. The one clean claim: *reproducible eval of a real fleet, failures published.*
- [ ] Land as `charm/modules/eval-harness/`; promote scorecard to repo front page + `EVIDENCE.md` (see `SLOT-IN-CHARM.md`).
- [ ] Harden the two real defects the benchmark found in *our own* fleet:
      - INV-2 → make independent VERIFY a hard precondition for **Tier-2** commit (leave Tier-0/1 advisory).
      - INV-3 → dedupe re-ACCEPT by (proposal, actor) in the consensus driver.
- [ ] Add per-agent token/latency accounting to the scorecard (events already carry `ts`).
- [ ] `adapters/` seam documented (done in draft); one reference adapter (consensus ledger) shipping.
- **Bar:** a stranger clones the repo, runs the eval, gets the same scorecard, and can dispute an
  invariant by editing `invariants.py`.

## v2 - CROSS-MODEL (amplifier)
- [ ] Real OpenAI-driven and Gemini-driven runs of the **same** coordination task, each scored via its own adapter.
- **Bar:** three scorecards (Claude/OpenAI/Gemini) on one task, no re-labelled logs. Until then, the
  schema claims neutrality and the runs do not - stated honestly.

## v3 - MORE TASK FAMILIES
- [ ] Long-horizon coding workflow corpus (implementer+reviewer, multi-file refactor).
- [ ] Research workflow corpus (fan-out→verify→synthesize).
- **Bar:** each family has its own invariants + a real, sanitized fixture that reproduces.
