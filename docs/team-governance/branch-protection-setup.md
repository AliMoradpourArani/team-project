# Protected `main` Setup

Configure repository rules/branch protection for `main` so the governance files in this repository are enforced rather than merely documented.

Recommended settings:

- require a pull request before merging,
- require at least 1 approving review,
- require review from CODEOWNERS,
- dismiss stale approvals when new commits materially change the PR,
- require the repository's CI/security status checks,
- require conversation resolution before merge when available,
- block force pushes,
- block branch deletion,
- restrict bypass to the Founder/Owner except documented emergencies.

`CODEOWNERS` contains `* @HoosseinRahimi`, so requiring CODEOWNER review makes the Founder/Owner a required reviewer for Core changes.

Normal developers should use GitHub **Write** access. Do not grant Maintain/Admin merely to let someone create branches, push feature branches, or open pull requests.

These settings are GitHub account/repository configuration and must be applied in GitHub repository settings or an organization ruleset. Keep this document synchronized with the configured rules.
