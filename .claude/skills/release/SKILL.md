---
name: release
description: Create a release PR with version bump and changelog
disable-model-invocation: true
argument-hint: version
---

Create a PR with branch name `release/v$ARGUMENTS` containing only these changes:

1. Update version in `pyproject.toml`
2. Ensure `TONGUES_VERSION` matches between `.github/workflows/ci.yml` and `.github/workflows/release.yml`
3. Add a new version column to the Releases table in `README.md` with download links (keep the previous version column)

No other changes—no refactors, no fixes, no documentation updates.

## Changelog

Generate release notes from commits since the last tag (or all commits if no tags):
```
git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline
```

Focus on what matters to users:
- New features and capabilities
- Breaking changes or behavior changes
- Group all bug fixes as "Various bug fixes" (don't itemize)
- Omit internal refactors, test changes, and CI updates

Put the changelog in the PR body. The workflow extracts it for the GitHub release.

Run `just check` before pushing. PR title: `Release v$ARGUMENTS`

## After merge

Tag, push, and clean up:
```
git checkout main && git pull && git tag v$ARGUMENTS && git push --tags && git push origin --delete release/v$ARGUMENTS
```

The tag triggers a workflow that creates the GitHub release with transpiled binaries (parable.py, parable.js, parable.pl).
