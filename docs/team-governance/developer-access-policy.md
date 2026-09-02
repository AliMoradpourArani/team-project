# ForgeFlow Developer Access Policy

This policy defines the operational controls for granting development access to the private `ForgeFlow-AI-Core` repository. It is an engineering and security policy, not a substitute for a signed legal agreement.

## 1. Principles

- Least privilege: developers receive only the access needed for their role.
- Private Core access is temporary and revocable.
- Repository contribution does not itself create equity, partnership, or ownership rights.
- Legal ownership/licensing is governed by the signed Developer/IP/Confidentiality Agreement.
- Signed contracts, identity documents, addresses, payment data, and other personal records must never be stored in this repository.

## 2. Required onboarding before access

Before inviting a developer to the private Core repository, record completion of:

1. identity/contact verification appropriate for the engagement,
2. signed Developer/IP/Confidentiality Agreement,
3. pre-existing IP disclosure,
4. approved role and scope of work,
5. acknowledgement of this Engineering/Security policy,
6. approved third-party/open-source exceptions, if any,
7. access authorization by the Founder/Owner.

Store the signed documents in the chosen e-signature/document system, not GitHub.

## 3. GitHub permissions

Default developer role: **Write**.

Do not grant **Maintain** or **Admin** to normal developers. Admin-level control remains with the Founder/Owner unless a separately authorized technical administrator is required.

Developers should:

- create feature/fix branches,
- open pull requests to `main`,
- respond to review feedback,
- run required tests and checks,
- avoid direct pushes to protected branches.

The Owner should configure `main` branch protection/rules to require:

- pull requests before merge,
- required CI/status checks,
- CODEOWNERS review,
- stale approval dismissal when the diff changes materially,
- blocked force pushes,
- blocked branch deletion.

## 4. CODEOWNERS

The repository-wide `* @HoosseinRahimi` rule identifies the Founder/Owner as code owner across the Core. Specific high-risk paths are also listed explicitly for audit clarity.

CODEOWNERS only becomes an enforced merge gate when the repository's branch protection/ruleset requires code-owner review.

## 5. Secrets and production access

Developers must not commit secrets. Production credentials must be managed through the relevant deployment/provider secret store.

Grant production, billing, domain, signing-key, deployment-admin, or organization-owner permissions only when the role requires them. Prefer narrowly scoped, individual accounts over shared credentials.

If a developer could access a credential that cannot be individually revoked, rotate it during offboarding.

## 6. Third-party and AI-assisted contributions

Before merge, contributors must identify any material not created specifically for ForgeFlow, including pre-existing code, copied snippets, models, datasets, fonts, assets, generated content, or dependencies with unusual licence terms.

Do not merge material with unclear rights or incompatible licence obligations. AI-assisted code receives the same provenance, security, confidentiality, licence, and quality review as human-written code.

## 7. Access review

Review private Core access periodically and whenever a person's role changes. Remove access that is no longer required.

Recommended access register fields:

- legal name,
- GitHub username,
- role,
- repository permission,
- production/deployment access,
- agreement signed date/version,
- access granted date,
- approver,
- last review date,
- access revoked date.

Do not commit the populated access register to this repository if it contains personal information.

## 8. Offboarding

When an engagement ends or Core access is no longer needed:

1. revoke GitHub repository access,
2. revoke deployment/cloud/CI/package-registry access,
3. revoke active sessions, SSH keys, app passwords, or service credentials where applicable,
4. rotate shared or exposed credentials,
5. transfer open branches/issues/PRs and operational knowledge,
6. obtain the required return/deletion acknowledgement for confidential material,
7. preserve signed agreements and the audit trail,
8. record the access-revocation date.

Local clones are not automatically erased when GitHub access is removed. Contractual return/deletion obligations therefore remain important.

## 9. Future incorporation

Until a company is incorporated and the IP chain is formally transferred, the Founder/Owner is the designated recipient/owner under the applicable agreements. When a company is formed, execute the required founder-to-company IP assignment and update new agreements to name the company directly.
