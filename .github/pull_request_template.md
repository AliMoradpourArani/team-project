## Summary

<!-- What changed and why? Keep this focused on one logical change. -->

## Scope

<!-- List the main files/features touched. Call out database, schema, CI, dependency, or security-sensitive changes explicitly. -->

## Verification

- [ ] Backend tests/lint pass when applicable
- [ ] Frontend lint/type/unit/build pass when applicable
- [ ] E2E behavior is covered or not applicable
- [ ] Fresh database init/sync still works when data/database code changed
- [ ] No secrets, generated databases, personal data, or unrelated files are included
- [ ] Documentation/contracts were updated if behavior changed
- [ ] New architecture decisions have an ADR when needed
- [ ] Feature branch is up to date with `main` (`git merge main`)

## Contribution and IP checks

- [ ] The required `ForgeFlow Legal Gate` is green or I am an explicitly exempt account
- [ ] I created this contribution for the authorized ForgeFlow engagement, or I disclosed relevant pre-existing material through the current Legal Pack process
- [ ] I did not add third-party code, models, datasets, fonts, assets, or dependencies without a compatible licence and project approval
- [ ] I did not copy confidential code or materials from another employer, client, university, or private repository
- [ ] Any AI-assisted code has been reviewed for provenance, licence risk, secrets, correctness, and security

> These PR checkboxes are an engineering reminder only. The versioned acceptance/evidence control is the `ForgeFlow Legal Gate` under `.github/legal/`. A dedicated e-signature agreement may additionally be required for higher-risk engagements.

### Member project integration (when this PR adds/changes `projects/<owner>/...`)

- [ ] `data/projects/<project_id>.json` matches the project owner/id
- [ ] `project.json`, README, repository path, typed runner, and entry point are included
- [ ] `make project-check PROJECT_ID=<project_id>` reports `READY`
- [ ] No member-specific Core route/component was added

## Risk and rollback

**Risk:** Low / Medium / High

<!-- What could break? How would we revert or recover? -->

## Screenshots / notes

<!-- Optional for visible UI changes or reviewer context. -->
