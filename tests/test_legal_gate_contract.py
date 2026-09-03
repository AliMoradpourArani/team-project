from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGAL_DIR = ROOT / ".github" / "legal"
WORKFLOW = ROOT / ".github" / "workflows" / "legal-gate.yml"

PACK_DOCS = (
    "FORGEFLOW_DEVELOPER_CONTRIBUTION_TERMS.md",
    "FORGEFLOW_DEVELOPER_IP_CONFIDENTIALITY_AGREEMENT.md",
    "FORGEFLOW_ENGINEERING_ACCESS_SECURITY_POLICY.md",
    "FORGEFLOW_PRE_EXISTING_IP_DISCLOSURE.md",
    "FORGEFLOW_OFFBOARDING_RETURN_DELETION_ACKNOWLEDGEMENT.md",
)


def test_legal_pack_version_matches_all_documents() -> None:
    version = (LEGAL_DIR / "AGREEMENT_VERSION").read_text(encoding="utf-8").strip()

    assert version
    for filename in PACK_DOCS:
        text = (LEGAL_DIR / filename).read_text(encoding="utf-8")
        assert version in text, filename


def test_legal_pack_contains_both_pre_existing_ip_paths() -> None:
    version = (LEGAL_DIR / "AGREEMENT_VERSION").read_text(encoding="utf-8").strip()
    terms = (LEGAL_DIR / "FORGEFLOW_DEVELOPER_CONTRIBUTION_TERMS.md").read_text(
        encoding="utf-8"
    )

    assert (
        f"I have read and accept the ForgeFlow Legal Pack v{version}. "
        "Pre-Existing IP: NONE."
    ) in terms
    assert (
        f"I have read and accept the ForgeFlow Legal Pack v{version}. "
        "Pre-Existing IP: DISCLOSED SEPARATELY."
    ) in terms


def test_iran_agreement_does_not_purport_to_waive_moral_rights() -> None:
    agreement = (
        LEGAL_DIR / "FORGEFLOW_DEVELOPER_IP_CONFIDENTIALITY_AGREEMENT.md"
    ).read_text(encoding="utf-8")

    assert "laws of the Islamic Republic of Iran" in agreement
    assert "does not" in agreement
    assert "assign or waive moral rights" in agreement
    assert "waives and agrees not to assert moral rights" not in agreement


def test_legal_gate_workflow_preserves_security_and_approval_contract() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "pull_request_target:" in workflow
    assert "issue_comment:" in workflow
    assert "statuses: write" in workflow
    assert "ForgeFlow Legal Gate" in workflow
    assert ".github/legal/AGREEMENT_VERSION" in workflow
    assert ".github/legal/FORGEFLOW_DEVELOPER_CONTRIBUTION_TERMS.md" in workflow
    assert "Pre-Existing IP: NONE." in workflow
    assert "Pre-Existing IP: DISCLOSED SEPARATELY." in workflow
    assert "ForgeFlow Pre-Existing IP Disclosure approved for @" in workflow
    assert "const founder = 'HoosseinRahimi';" in workflow

    # pull_request_target runs with base-repository privileges. The legal gate must
    # never check out or execute code from an untrusted PR head.
    assert "actions/checkout" not in workflow
