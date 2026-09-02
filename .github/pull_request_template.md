## Summary

<!-- What changed and why? Keep this focused on one logical change. -->

## Scope

<!-- List the main files/features touched. Call out database, schema, CI, dependency, or security-sensitive changes explicitly. -->

## Verification

- [ ] Backend tests/lint pass when applicable
- [ ] Frontend lint/type/unit/build pass when applicable
- [ ] E2E behavior is covered or not applicable
- [ ] Fresh database init/sync still works when data/database code changed
- [ ] No secrets, generated databases, or unrelated files are included
- [ ] Documentation/contracts were updated if behavior changed
- [ ] New architecture decisions have an ADR when needed
- [ ] Feature branch is up to date with `main` (`git merge main`)

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
