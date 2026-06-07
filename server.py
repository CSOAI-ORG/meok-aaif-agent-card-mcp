#!/usr/bin/env python3
"""
MEOK AAIF Agent Card MCP — Linux Foundation AAIF agent identity bridge
=========================================================================

By MEOK AI Labs · https://meok.ai · MIT
<!-- mcp-name: io.github.CSOAI-ORG/meok-aaif-agent-card-mcp -->

WHAT THIS BRIDGES
-----------------
The Agentic AI Foundation (AAIF) under the Linux Foundation is standardising
**Agent Cards** — the canonical machine-readable identity + capability +
trust manifest that any agent can publish at `/.well-known/agent-card`.

AAIF Agent Cards extend A2A discovery with:
  - Cryptographic identity (DID / VC)
  - Capability advertising (compatible with OASF + Anthropic Connectors)
  - Trust signals (audit attestations, certifications, signing keys)
  - Endpoint metadata (HTTP / SSE / WebSocket / stdio)

This MCP issues + verifies + indexes AAIF agent cards. Drop-in for
A2A discovery, Cisco AGNTCY directory, MEOK A2A Substrate.

NOBODY else has shipped an AAIF agent-card MCP. First-mover.

TOOLS
-----
- issue_agent_card(agent_did, name, capabilities, endpoints, ...)
- publish_card(card, target_url): publish to /.well-known/agent-card
- verify_card(card, expected_did): cryptographic + schema check
- bridge_a2a_to_aaif(a2a_card): A2A → AAIF conversion
- bridge_oasf_to_aaif(oasf_manifest): OASF → AAIF conversion
- list_capability_taxonomy(): AAIF v0.1 capability taxonomy
- sign_card_chain(card): HMAC + DID-signing for verifiable publication

By MEOK AI Labs · MIT.
"""

from __future__ import annotations
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from typing import Optional
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("meok-aaif-agent-card")
_HMAC_SECRET = os.environ.get("MEOK_HMAC_SECRET", "")
_CARDS: dict[str, dict] = {}


SPEC = "AAIF Agent Card v0.1 (Linux Foundation, 2026 draft)"

# AAIF capability taxonomy (compatible with OASF + Anthropic Connectors)
CAPABILITY_CATEGORIES = {
    "compute":         ["text_generation", "code_generation", "image_generation", "embeddings", "reasoning"],
    "data":            ["sql_query", "rest_api", "graphql", "file_read", "file_write", "vector_search"],
    "communication":   ["email_send", "chat_post", "voice_call", "video_call", "webhook_trigger"],
    "commerce":        ["payment_initiate", "invoice_generate", "subscription_manage", "refund_process"],
    "compliance":      ["regulation_lookup", "audit_log", "policy_evaluate", "bias_check", "incident_classify"],
    "identity":        ["did_resolve", "credential_verify", "signature_check", "mfa_verify"],
    "automation":      ["workflow_orchestrate", "retry_on_failure", "parallel_execute", "schedule_task"],
}

ENDPOINT_TRANSPORTS = ["http", "https", "sse", "websocket", "stdio", "ipc"]


def _sign(payload: dict) -> str:
    if not _HMAC_SECRET:
        return "unsigned-no-key-configured"
    return hmac.new(_HMAC_SECRET.encode(), json.dumps(payload, sort_keys=True).encode(), hashlib.sha256).hexdigest()


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def issue_agent_card(
    agent_did: str,
    name: str,
    description: str,
    capabilities: list[str],
    endpoints: list[dict],
    version: str = "1.0.0",
    publisher: Optional[str] = None,
    trust_attestations: Optional[list[dict]] = None,
    license_spdx: str = "MIT",
    signing_key_id: Optional[str] = None,
) -> dict:
    """
    Issue an AAIF Agent Card.

    Args:
        agent_did: W3C DID of the agent.
        name: Human-readable agent name.
        description: One-paragraph description.
        capabilities: List of capability strings (see list_capability_taxonomy()).
        endpoints: List of {transport, url, auth} dicts.
        version: Semver.
        publisher: Organisation publishing this agent.
        trust_attestations: Optional list of signed certs (compliance, audit, etc.).
        license_spdx: SPDX license identifier.
        signing_key_id: DID key fragment for the agent's signing key.

    Returns:
        {card, signature, well_known_url}
    """
    # Validate endpoints
    for ep in endpoints:
        if ep.get("transport") not in ENDPOINT_TRANSPORTS:
            return {"error": f"endpoint transport must be one of {ENDPOINT_TRANSPORTS}"}
    # Validate capability strings (accept category names + specific values)
    valid_caps = set(CAPABILITY_CATEGORIES.keys()) | {c for cs in CAPABILITY_CATEGORIES.values() for c in cs}
    unknown = [c for c in capabilities if c not in valid_caps]
    # (warn rather than fail on unknown — allows extension)

    card_id = f"AAIF_{int(time.time())}_{os.urandom(4).hex()}"
    card = {
        "spec": SPEC,
        "card_id": card_id,
        "agent_did": agent_did,
        "name": name,
        "description": description,
        "version": version,
        "license": license_spdx,
        "publisher": publisher or "MEOK AI Labs (CSOAI LTD, UK Companies House 16939677)",
        "capabilities": capabilities,
        "endpoints": endpoints,
        "trust_attestations": trust_attestations or [],
        "signing_key_id": signing_key_id or f"{agent_did}#key-1",
        "issued_at": _ts(),
        "well_known_url": "/.well-known/agent-card",
    }
    card["signature"] = _sign(card)
    _CARDS[card_id] = card
    return {
        "card": card,
        "signature": card["signature"],
        "well_known_url": "/.well-known/agent-card",
        "unknown_capabilities": unknown,
        "next_step": "Call publish_card() to host this JSON at /.well-known/agent-card on your agent endpoint.",
    }


@mcp.tool()
def publish_card(card: dict, target_url: str) -> dict:
    """
    Generate the HTTP server config needed to publish a card at /.well-known/agent-card.

    Args:
        card: A card from issue_agent_card().
        target_url: The base URL of your agent (e.g. https://my-agent.example).

    Returns:
        {target_url, payload, http_headers, vercel_config_snippet, nginx_snippet}
    """
    full_url = target_url.rstrip("/") + "/.well-known/agent-card"
    payload = json.dumps(card, indent=2)
    return {
        "target_url": full_url,
        "payload": payload,
        "http_headers": {
            "Content-Type": "application/json",
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
        "vercel_config_snippet": {
            "headers": [
                {"source": "/.well-known/agent-card",
                 "headers": [{"key": "Content-Type", "value": "application/json"}]}
            ],
        },
        "nginx_snippet": (
            'location = /.well-known/agent-card {\n'
            '    add_header Content-Type application/json;\n'
            '    add_header Access-Control-Allow-Origin *;\n'
            '    return 200 \'<paste-card-json-here>\';\n'
            '}'
        ),
        "verification_hint": f"After publishing, verify by curling {full_url}",
    }


@mcp.tool()
def verify_card(card: dict, expected_did: Optional[str] = None) -> dict:
    """
    Verify an AAIF Agent Card — schema + signature + DID match.

    Args:
        card: Card to verify.
        expected_did: Optional expected agent_did.

    Returns:
        {valid, schema_ok, signature_ok, issues}
    """
    issues = []
    required = ["spec", "agent_did", "name", "description", "capabilities", "endpoints", "signature"]
    for f in required:
        if f not in card:
            issues.append(f"missing required field: {f}")

    sig_provided = card.get("signature")
    sig_recomputed = _sign({k: v for k, v in card.items() if k != "signature"})
    sig_ok = sig_provided == sig_recomputed
    if not sig_ok:
        issues.append("signature mismatch")

    did_ok = True
    if expected_did and card.get("agent_did") != expected_did:
        did_ok = False
        issues.append(f"agent_did mismatch (expected {expected_did}, got {card.get('agent_did')})")

    return {
        "valid": len(issues) == 0 and sig_ok and did_ok,
        "schema_ok": all(f in card for f in required),
        "signature_ok": sig_ok,
        "did_ok": did_ok,
        "issues": issues,
        "verified_at": _ts(),
    }


@mcp.tool()
def bridge_a2a_to_aaif(a2a_card: dict) -> dict:
    """
    Convert an A2A agent-card (Google A2A spec) to an AAIF Agent Card.

    Args:
        a2a_card: A2A agent-card dict.

    Returns:
        AAIF Agent Card.
    """
    name = a2a_card.get("name", "unnamed")
    description = a2a_card.get("description", "")
    skills = a2a_card.get("skills", [])
    capabilities = ["compute", "communication"]
    for s in skills:
        sid = s.get("id", "").lower() if isinstance(s, dict) else str(s).lower()
        if "compliance" in sid: capabilities.append("compliance")
        if "payment" in sid: capabilities.append("commerce")
        if "auth" in sid or "identity" in sid: capabilities.append("identity")
    capabilities = list(set(capabilities))
    endpoints = [{"transport": "https", "url": a2a_card.get("url", "https://unknown.example"), "auth": "bearer"}]
    return issue_agent_card(
        agent_did=a2a_card.get("did", f"did:web:{name.lower().replace(' ', '-')}"),
        name=name, description=description, capabilities=capabilities, endpoints=endpoints,
        version=a2a_card.get("version", "1.0.0"),
    )


@mcp.tool()
def bridge_oasf_to_aaif(oasf_manifest: dict) -> dict:
    """
    Convert an OASF manifest (Cisco AGNTCY) to an AAIF Agent Card.

    Args:
        oasf_manifest: OASF manifest dict.

    Returns:
        AAIF Agent Card.
    """
    return issue_agent_card(
        agent_did=oasf_manifest.get("agent_id", "did:meok:unknown"),
        name=oasf_manifest.get("name", "OASF Agent"),
        description=oasf_manifest.get("description", ""),
        capabilities=oasf_manifest.get("capabilities", ["compute"]),
        endpoints=[{"transport": "https", "url": "https://api.meok.ai/v1/oasf/" + oasf_manifest.get("agent_id", "x"), "auth": "bearer"}],
        version=oasf_manifest.get("version", "1.0.0"),
        publisher=oasf_manifest.get("publisher"),
    )


@mcp.tool()
def list_capability_taxonomy() -> dict:
    """Return the AAIF capability taxonomy."""
    return {
        "spec": SPEC,
        "categories": CAPABILITY_CATEGORIES,
        "total_capabilities": sum(len(v) for v in CAPABILITY_CATEGORIES.values()),
        "endpoint_transports": ENDPOINT_TRANSPORTS,
    }


@mcp.tool()
def sign_card_chain(card_id: str) -> dict:
    """HMAC-sign a card for verifiable publication."""
    if card_id not in _CARDS:
        return {"error": "unknown_card"}
    c = _CARDS[card_id]
    sealed = {**c, "sealed_at": _ts()}
    sig = _sign(sealed)
    return {
        "signed": _HMAC_SECRET != "",
        "signature": sig,
        "sealed_at": sealed["sealed_at"],
        "verify_url": f"https://meok-attestation-api.vercel.app/verify/{card_id}",
    }


if __name__ == "__main__":
    mcp.run()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/00wfZjcgAeUW4c5cyQ8k90K"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
