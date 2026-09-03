# Protected `main` Setup

Configure repository rules/branch protection for `main` so the governance files in this repository are enforced rather than merely documented.

Recommended settings:

- require a pull request before merging,
- require at least 1 approving review,
- require review from CODEOWNERS,
- dismiss stale approvals when new commits materially change the PR,
- require the repository's CI/security status checks,
- require the exact commit-status context **`ForgeFlow Legal Gate`**,
- require conversation resolution before merge when available,
- block force pushes,
- block branch deletion,
- restrict bypass to the Founder/Owner except documented emergencies.

`CODEOWNERS` contains `* @HoosseinRahimi`, so requiring CODEOWNER review makes the Founder/Owner a required reviewer for Core changes.

## Legal Gate status

`.github/workflows/legal-gate.yml` writes a custom commit status named exactly:

`ForgeFlow Legal Gate`

For a non-exempt contributor the status remains pending until the PR author has posted the exact acceptance sentence for the current agreement version from the same GitHub account. The status becomes success once acceptance is found.

The required rule must reference this custom commit-status context, not merely the Actions workflow run name. Without the required status rule, the automation still records acceptance but cannot technically prevent a merge by an administrator or other bypass-capable actor.

Normal developers should use GitHub **Write** access. Do not grant Maintain/Admin merely to let someone create branches, push feature branches, or open pull requests.

These settings are GitHub account/repository configuration and must be applied in GitHub repository settings or an organization ruleset. Keep this document synchronized with the configured rules.
