# adapters/ - the cross-model seam (v2 lands here)

An **adapter** maps one agent runtime's raw events onto the nine `type`s of the tracekit trace schema
(`schema/trace-event.schema.json`). Because the schema is provider-neutral, the *scorer never
changes* - only the adapter does. This directory is the seam that lets a Claude run, an OpenAI run,
and a Gemini run be scored by the *same* invariants.

**Status (v1):** one real reference adapter ships; cross-model is v2. See `ADAPTER-ANGLE.md` for why
that boundary is deliberate (shipping a half-real cross-model claim is worse than shipping the seam).

## Reference adapter (real, shipping in v1)

`../tracekit/sanitize.py` **is** the reference adapter: consensus-ledger events → tracekit trace
events (whitelist projection + identity normalisation). It is the proof that the seam works on real
data end-to-end.

## Adapter interface (contract for v2 adapters)

```
def adapt(raw_events: Iterable[dict]) -> Iterable[dict]:
    """Yield tracekit trace events. Each MUST carry:
        event_id, proposal_id, type (one of the 9 enum values), actor, ts
    and SHOULD carry risk_tier when the runtime has a notion of risk.
    Map the runtime's lifecycle onto:
        PROPOSE  - an agent proposes an action/decision/subtask
        ACCEPT   - a peer agrees
        COUNTER  - a peer proposes an alternative
        REJECT   - a peer refuses
        VERIFY   - an agent independently checks another's work
        COMMIT   - the decision becomes 'of record' / the action is taken
        ESCALATE - handed to a human/leader to decide
        HUMAN_APPROVED - a human explicitly approved a risky action
        CLARIFY  - a request for missing information
    """
```

## v2 acceptance bar (falsifiable, from ADAPTER-ANGLE.md)

> v2 ships when the **same** coordination task has a **real** OpenAI run and a **real** Gemini run,
> each producing its own scorecard through its own adapter. No re-labelled Claude logs.
