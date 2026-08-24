---
title: Releases
description: Release-please, PyPI trusted publishing, and Sourcey Pages delivery.
---

# Releases

Versioning and `CHANGELOG.md` are owned by release-please. Merge Conventional
Commits to `main`; release-please opens a release pull request with the next
version and generated notes. That PR is merged with a merge commit.

After the release tag exists, trusted GitHub Actions build the wheel and sdist,
publish to PyPI through OIDC trusted publishing, and rebuild the Sourcey site
from trusted `main` state for GitHub Pages. Pull-request jobs never publish a
package or deploy docs.

Before treating a release as complete, verify the GitHub Release, PyPI version,
wheel and sdist metadata, `content-gen --help`, and the deployed documentation
site including its generated `llms.txt`, `llms-full.txt`, and sitemap.

The package requires the released `vendor-fabric[meshy]>=2.2.0,<3` contract.
Publish any required `vendor-fabric` release first, then release this package,
then update downstream consumers to the released generator version.
