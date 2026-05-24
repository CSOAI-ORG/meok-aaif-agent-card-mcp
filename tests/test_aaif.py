"""Smoke tests for meok-aaif-agent-card-mcp."""
import sys, os, inspect, traceback
# Set HMAC secret BEFORE importing server so signatures are content-bound (not stub)
os.environ.setdefault("MEOK_HMAC_SECRET", "test-only-secret-for-smoke-tests")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    issue_agent_card,
    publish_card,
    verify_card,
    bridge_a2a_to_aaif,
    bridge_oasf_to_aaif,
    list_capability_taxonomy,
    sign_card_chain,
    _CARDS,
)


def test_issue_card_basic():
    _CARDS.clear()
    r = issue_agent_card(
        agent_did="did:web:test-agent.example",
        name="Test Agent",
        description="A test",
        capabilities=["compute", "communication"],
        endpoints=[{"transport": "https", "url": "https://test-agent.example", "auth": "bearer"}],
    )
    assert r["card"]["card_id"].startswith("AAIF_")
    assert "signature" in r["card"]


def test_issue_card_bad_endpoint_transport():
    _CARDS.clear()
    r = issue_agent_card(
        agent_did="did:x", name="x", description="x",
        capabilities=["compute"],
        endpoints=[{"transport": "carrier_pigeon", "url": "x"}],
    )
    assert "error" in r


def test_publish_card_returns_vercel_config():
    _CARDS.clear()
    r = issue_agent_card("did:web:x", "x", "x", ["compute"], [{"transport": "https", "url": "https://x.example"}])
    p = publish_card(r["card"], "https://x.example")
    assert "/.well-known/agent-card" in p["target_url"]
    assert "vercel_config_snippet" in p


def test_verify_card_round_trip():
    _CARDS.clear()
    r = issue_agent_card("did:web:x", "x", "x", ["compute"], [{"transport": "https", "url": "https://x.example"}])
    v = verify_card(r["card"], expected_did="did:web:x")
    assert v["valid"] is True
    assert v["signature_ok"] is True


def test_verify_card_detects_did_mismatch():
    _CARDS.clear()
    r = issue_agent_card("did:web:a", "x", "x", ["compute"], [{"transport": "https", "url": "https://x.example"}])
    v = verify_card(r["card"], expected_did="did:web:b")
    assert v["valid"] is False
    assert v["did_ok"] is False


def test_verify_card_detects_tampering():
    _CARDS.clear()
    r = issue_agent_card("did:web:x", "x", "x", ["compute"], [{"transport": "https", "url": "https://x.example"}])
    r["card"]["name"] = "TAMPERED"
    v = verify_card(r["card"])
    assert v["signature_ok"] is False


def test_bridge_a2a_to_aaif():
    _CARDS.clear()
    a2a = {"name": "Pay Agent", "description": "x", "url": "https://payagent.example",
           "skills": [{"id": "payment_initiate"}], "version": "1.0.0"}
    r = bridge_a2a_to_aaif(a2a)
    assert "commerce" in r["card"]["capabilities"]


def test_bridge_oasf_to_aaif():
    _CARDS.clear()
    oasf = {"agent_id": "did:x", "name": "Audit Agent", "description": "x",
            "capabilities": ["compliance", "audit_log"], "version": "1.0.0"}
    r = bridge_oasf_to_aaif(oasf)
    assert "compliance" in r["card"]["capabilities"]


def test_list_capability_taxonomy():
    r = list_capability_taxonomy()
    assert "compute" in r["categories"]
    assert r["total_capabilities"] > 10


def test_sign_card_chain():
    _CARDS.clear()
    r = issue_agent_card("did:web:x", "x", "x", ["compute"], [{"transport": "https", "url": "https://x.example"}])
    s = sign_card_chain(r["card"]["card_id"])
    assert "signature" in s


if __name__ == "__main__":
    g = dict(globals())
    fns = [v for k, v in g.items() if k.startswith("test_") and inspect.isfunction(v)]
    p = f = 0
    for fn in fns:
        try:
            fn(); print(f"OK {fn.__name__}"); p += 1
        except Exception as e:
            print(f"X  {fn.__name__}: {type(e).__name__}: {e}"); traceback.print_exc(); f += 1
    print(f"\n{p} passed, {f} failed")
