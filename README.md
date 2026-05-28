# MEOK AAIF Agent Card MCP

> ## 🧱 Part of the MEOK A2A Substrate (£999/mo)
> See [meok.ai/a2a](https://meok.ai/a2a).

# Linux Foundation AAIF agent identity bridge — /.well-known/agent-card

<!-- mcp-name: io.github.CSOAI-ORG/meok-aaif-agent-card-mcp -->

[![PyPI](https://img.shields.io/pypi/v/meok-aaif-agent-card-mcp)](https://pypi.org/project/meok-aaif-agent-card-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## What this bridges

The **Agentic AI Foundation (AAIF)** under the Linux Foundation is standardising **Agent Cards** — the canonical machine-readable identity + capability + trust manifest that any agent publishes at `/.well-known/agent-card`.

AAIF Agent Cards extend A2A discovery with:
- Cryptographic identity (DID / VC)
- Capability advertising (compatible with OASF + Anthropic Connectors)
- Trust signals (audit attestations, certifications, signing keys)
- Endpoint metadata (HTTP / SSE / WebSocket / stdio / IPC)

**Nobody else has shipped an AAIF Agent Card MCP.** First-mover.

## Tools

| Tool | Purpose |
|---|---|
| `issue_agent_card(agent_did, name, capabilities, endpoints, ...)` | Issue signed AAIF Agent Card |
| `publish_card(card, target_url)` | HTTP server config for `/.well-known/agent-card` |
| `verify_card(card, expected_did?)` | Schema + signature + DID check |
| `bridge_a2a_to_aaif(a2a_card)` | A2A agent-card → AAIF |
| `bridge_oasf_to_aaif(oasf_manifest)` | Cisco OASF manifest → AAIF |
| `list_capability_taxonomy()` | AAIF v0.1 capability taxonomy |
| `sign_card_chain(card_id)` | HMAC + DID-signing for verifiable publication |

## Why this matters

A2A, OASF, and AAIF agent cards all do almost the same thing — but with subtle schema differences. Building agents that discover each other across all three specs is a nightmare. This MCP normalises everything to AAIF + bridges from A2A + OASF automatically, so your agents are discoverable everywhere with one publish action.

## Sister MCPs

- `oasf-agent-directory-mcp` — Cisco AGNTCY directory bridge
- `agent-identity-trust-mcp` — W3C DID + VC + trust scoring
- `eudi-wallet-mcp` — EU Digital Identity Wallet bridge
- `mcp-spec-compliance-mcp` — validate your MCP server.json

Full catalogue: [meok.ai/anthropic-registry](https://meok.ai/anthropic-registry)

## Pricing

| Option | Price |
|---|---|
| Self-host MIT | £0 |
| Universal PAYG | £29/mo + £0.0002/call |
| A2A Substrate | £999/mo |
| Defence | £4,990/mo |

Buy: https://meok.ai/a2a

## Wire it up — full stack

See [meok.ai/mcp-stack](https://meok.ai/mcp-stack) for the 6-MCP chain.

## Licence

MIT. By [MEOK AI Labs](https://meok.ai) (CSOAI LTD, UK Companies House 16939677).

<!-- BUY-LADDER:START -->

## 💸 Try MEOK in 30 seconds — instant buy ladder

| Tier | Price | What you get | Stripe |
|---|---|---|---|
| Smoke test | **£1** | Signed sample MCP-Hardening report + Article 50 PDF | <https://buy.stripe.com/dRmcN75ScdQS7oh1Uc8k90U> |
| Quick Kit | **£9** | EU AI Act Article 50 implementation guide (C2PA + EU-Icon) | <https://buy.stripe.com/cNi00la8s1460ZT0Q88k90V> |
| Founder Call | **£29** | 30-min 1-on-1 with the founder | <https://buy.stripe.com/8x228ta8s6oqbExaqI8k90W> |

> Refundable. UK Stripe — VAT-clean. Builds on the 81-MCP MEOK fleet.
> Verify any signed report at <https://meok.ai/verify>.

<!-- BUY-LADDER:END -->

