# ForgeFlow Legal Gate

This directory contains the minimum repository-level contribution acknowledgement used by the private ForgeFlow Core repository.

## How the gate works

1. A non-exempt contributor opens or updates a pull request.
2. `.github/workflows/legal-gate.yml` checks whether that GitHub user has posted the exact acceptance statement for the current `AGREEMENT_VERSION` on a pull request authored by that same user.
3. If no acceptance exists, the workflow posts the current agreement link and exact acceptance statement and sets commit status **`ForgeFlow Legal Gate`** to `pending` on the PR head SHA.
4. When the PR author posts the exact statement, the workflow records the GitHub comment URL/timestamp through GitHub's normal audit trail and sets the commit status to `success`.
5. Later PRs from the same GitHub user reuse that acceptance while the version remains unchanged.
6. Changing `AGREEMENT_VERSION` invalidates prior acceptance automatically and requires a new statement.

## Required repository rule

The automation blocks merge only when repository rules require the exact commit-status context:

`ForgeFlow Legal Gate`

Do not confuse this custom commit status with the Actions workflow run itself.

Also require normal CI/Security checks, pull requests, CODEOWNER review and block force pushes to `main`.

## Source of truth

The gate intentionally does **not** trust a PR label as proof of acceptance. A contributor with repository Write access may be able to manipulate labels. Acceptance is found only when:

- the acceptance comment is authored by the same GitHub account that authored the PR,
- the PR containing that comment is also authored by that user,
- the comment text exactly matches the current agreement version.

## Exempt accounts

The current workflow exempts the repository founder account and standard automation bots. Review the exemption list whenever repository ownership or automation changes.

## Legal limits

This is a repository governance and evidence mechanism, not a guarantee that a GitHub comment qualifies as a secure electronic signature in every legal dispute. It does not waive mandatory rights under Iranian labour or other mandatory law, and it does not transfer non-transferable moral rights.

For higher-value engagements, sensitive IP, equity discussions, or disputed worker classification, use the fuller signed onboarding documents in addition to this gate.

## Version changes

When the legal text changes materially:

1. update `FORGEFLOW_DEVELOPER_CONTRIBUTION_TERMS.md`,
2. change `AGREEMENT_VERSION`,
3. update the exact version embedded in the agreement acceptance sentence,
4. merge both changes together.

The next PR from every non-exempt contributor will then require fresh acceptance.
