# Privacy and Data Safety

This framework runs on deeply personal data: notes, messages, contacts, call transcripts. Open-sourcing it safely means one hard rule.

## The rule: code out, data home

We publish the **framework**. We never publish the **data**. Your vault, contacts, secrets, and message history stay on your own machine.

## Do-not-publish list

Never commit any of the following, in code, docs, screenshots, or example files:

- Real names, emails, phone numbers, handles.
- Chat logs, emails, message transcripts.
- API keys, tokens, passwords, credentials, config with secrets.
- Timestamps, geo-data, or any metadata that could identify a real person.

Note: even "fake-looking" data can be personal data under GDPR if it is traceable to a real individual. Assume realistic examples can be reverse-engineered. Use clearly invented placeholders.

## Examples are synthetic

Everything under `/examples` is fabricated: placeholder personas (`Alice Example`, `agent://researcher-01`), `example.com` addresses, random vectors. No real account, no real transcript.

## Pre-commit checklist

- [ ] No secrets (keys, passwords, credentials, real config files).
- [ ] No PII (names, emails, addresses) in data files or docs.
- [ ] Example data only (fabricated or public-domain).
- [ ] No proprietary or confidential third-party data.
- [ ] README states "No real personal data is included".
- [ ] Run a PII scanner over text and review screenshots/diagrams by hand.

## Self-hosting

When you run this on your own data, nothing leaves your machine unless you explicitly send it (e.g. an optional external LLM call). Local-first is the default.
