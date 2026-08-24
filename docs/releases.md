---
title: Releases
description: Release-please, PyPI trusted publishing, and Sourcey Pages delivery.
---

# Releases

Versioning and `CHANGELOG.md` are owned by release-please. Merge Conventional
Commits to `main`; release-please opens a release pull request with the next
version and generated notes. That PR is merged with a merge commit.

After the release tag exists, the trusted release workflow calls the single CD
workflow once. CD builds the wheel and sdist, publishes to PyPI through OIDC
trusted publishing, and rebuilds the Sourcey site from the release tag for
GitHub Pages. It is intentionally not also triggered by the GitHub Release
event: duplicate delivery runs can race a Pages deployment or attempt to
publish the same artifact twice. Pull-request jobs never publish a package or
deploy docs.

When release-please creates a release pull request, the release workflow also
refreshes `uv.lock` on that canonical branch before auto-merge. This keeps the
version in `pyproject.toml` and the locked editable package record aligned
without granting release credentials to pull-request workflows.

Before treating a release as complete, verify the GitHub Release, PyPI version,
wheel and sdist metadata, `content-gen --help`, and the deployed documentation
site including its generated `llms.txt`, `llms-full.txt`, and sitemap.

The package requires the released `vendor-fabric[meshy]>=2.2.0,<3` contract.
Publish any required `vendor-fabric` release first, then release this package,
then update downstream consumers to the released generator version.
