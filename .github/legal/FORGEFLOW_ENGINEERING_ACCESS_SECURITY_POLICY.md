# ForgeFlow Engineering Access & Security Policy

**Legal Pack Version:** `2026-09-IR-2`

This policy governs technical access and development behavior for private ForgeFlow systems. It supports the Developer/IP/Confidentiality Agreement and does not replace mandatory employment or security obligations.

## 1. Least-privilege access

Normal developers should receive the minimum role needed to contribute. For `ForgeFlow-AI-Core`, the normal role is **Write**. Maintain/Admin, organization ownership, billing, signing-key and production-admin privileges require separate explicit approval.

Access is personal, temporary and revocable. Shared accounts and shared long-lived credentials should be avoided.

## 2. Branch and review workflow

Do not develop normal features directly on `main`. Use a feature/fix branch, open a pull request, run required checks, address review feedback and obtain required CODEOWNER approval before merge.

Do not bypass branch rules, force-push protected branches, disable checks or self-merge around required review controls unless the Founder explicitly authorizes an emergency procedure.

## 3. Secrets and confidential data

Never commit API keys, tokens, passwords, private keys, production credentials, personal data, customer data, signed agreements or identity records.

Do not paste ForgeFlow secrets or confidential source into public AI tools, public issue trackers, paste sites, forums or unapproved third-party services.

## 4. Third-party and open-source material

Before adding a dependency or external asset, confirm that its licence is compatible with intended ForgeFlow use. Copyleft, source-available, non-commercial, research-only, custom or unclear licences require explicit review.

Do not copy code or confidential materials from another employer, client, university, private repository or proprietary product.

## 5. AI-assisted development

AI-assisted code is not automatically approved. Review provenance, licence risk, security, correctness, tests, maintainability and confidentiality before merge.

Do not disclose secrets, personal data, customer data or restricted third-party information to an AI provider unless authorized.

## 6. Local copies and devices

Keep devices reasonably secured with account authentication and current security updates. Do not leave private repositories or credentials on shared or public devices.

Local clones remain confidential after repository access is revoked and must be returned or deleted when required by the applicable agreement.

## 7. Incidents

Promptly report lost devices, leaked credentials, accidental public commits, suspicious account activity, unapproved disclosure, malware or data exposure to the Founder. Do not hide or silently repair an incident that may require credential rotation or audit.

## 8. Offboarding

When access ends, stop using ForgeFlow systems, transfer active work, return or delete confidential material as required and complete the offboarding confirmation. The Founder will revoke repository and service access and rotate shared or exposed credentials as needed.

## 9. Acknowledgement

Acceptance of the current ForgeFlow Legal Pack confirms that the Developer has read and agrees to follow this policy while using ForgeFlow systems.