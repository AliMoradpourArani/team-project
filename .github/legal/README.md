# ForgeFlow Legal Gate

This directory contains the versioned legal/security acknowledgement used by private ForgeFlow Core contributors.

## Current Legal Pack

The current version is stored in `AGREEMENT_VERSION` and covers:

- `FORGEFLOW_DEVELOPER_IP_CONFIDENTIALITY_AGREEMENT.md`
- `FORGEFLOW_ENGINEERING_ACCESS_SECURITY_POLICY.md`
- `FORGEFLOW_PRE_EXISTING_IP_DISCLOSURE.md`
- `FORGEFLOW_OFFBOARDING_RETURN_DELETION_ACKNOWLEDGEMENT.md`
- `FORGEFLOW_DEVELOPER_CONTRIBUTION_TERMS.md` as the acceptance cover/summary

## How the gate works

1. A non-exempt contributor opens or updates a pull request.
2. `.github/workflows/legal-gate.yml` reads the Legal Pack version from the PR base branch.
3. The contributor must have posted one exact current-version acceptance statement on a pull request authored by that same GitHub account.
4. The statement must declare either `Pre-Existing IP: NONE` or `Pre-Existing IP: DISCLOSED SEPARATELY`.
5. If `NONE`, acceptance can pass immediately.
6. If `DISCLOSED SEPARATELY`, the gate stays pending until `@HoosseinRahimi` posts the exact version/user-specific approval statement on that PR after receiving the separate disclosure record.
7. Successful acceptance is reusable for later PRs while the Legal Pack version remains unchanged.
8. Changing `AGREEMENT_VERSION` invalidates prior acceptance and requires fresh acknowledgement.

## Required repository rule

Repository rules must require the exact commit-status context:

`ForgeFlow Legal Gate`

Also require normal CI/Security checks, pull requests, CODEOWNER review and block force pushes to `main`.

## Evidence and privacy model

The gate does not trust PR labels as proof. Acceptance is recognized only when the comment is authored by the same GitHub account that authored the PR containing it.

For the `DISCLOSED SEPARATELY` path, only `@HoosseinRahimi` can provide the additional owner-approval comment recognized by the gate.

Do not place identity documents, home addresses, compensation records, signed HR documents, private repository contents or detailed confidential IP disclosures in GitHub. Keep those records in a private legal/HR/document system.

## Exempt accounts

The current workflow exempts the Founder account and standard automation bots. Review the exemption list whenever repository ownership or automation changes.

## Security contract

The workflow uses privileged GitHub events but must never check out or execute untrusted PR-head code. Contract tests enforce the no-checkout invariant and Legal Pack version relationships.

## Legal limits

This is a repository governance and electronic-evidence mechanism. It does not guarantee that a GitHub comment qualifies as a secure electronic signature for every legal purpose. It does not waive mandatory Iranian labour protections or transfer non-transferable moral rights.

A dedicated e-signature service remains appropriate for higher-value engagements, sensitive IP, disputed worker classification or where stronger evidentiary assurance is needed.

## Version changes

For a material Legal Pack change:

1. update all affected Legal Pack documents;
2. change `AGREEMENT_VERSION`;
3. update version strings and acceptance statements in the pack;
4. update the Legal Gate contract tests;
5. merge all changes together.

The next PR from every non-exempt contributor will then require fresh acceptance.