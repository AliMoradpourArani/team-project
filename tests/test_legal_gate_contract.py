from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGAL_DIR = ROOT / ".github" / "legal"
WORKFLOW = ROOT / ".github" / "workflows" / "legal-gate.yml"


def test_legal_gate_version_matches_terms() -> None:
    version = (LEGAL_DIR / "AGREEMENT_VERSION").read_text(encoding="utf-8").strip()
    terms = (LEGAL_DIR / "FORGEFLOW_DEVELOPER_CONTRIBUTION_TERMS.md").read_text(
        encoding="utf-8"
    )

    assert version
    assert f"**Version:** `{version}`" in terms
    assert (
        f"I have read and accept the ForgeFlow Developer Contribution Terms v{version}."
        in terms
    )


def test_legal_gate_workflow_preserves_security_contract() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "pull_request_target:" in workflow
    assert "issue_comment:" in workflow
    assert "statuses: write" in workflow
    assert "ForgeFlow Legal Gate" in workflow
    assert ".github/legal/AGREEMENT_VERSION" in workflow
    assert ".github/legal/FORGEFLOW_DEVELOPER_CONTRIBUTION_TERMS.md" in workflow

    # pull_request_target runs with base-repository privileges. The legal gate must
    # never check out or execute code from an untrusted PR head.
    assert "actions/checkout" not in workflow
