---
title: Contributing
description: Development setup, validation gates, and contribution expectations.
---

# Contributing

This project accepts changes through pull requests. Use Conventional Commit
messages (`feat:`, `fix:`, `docs:`, `test:`, `ci:`, and so on), keep the
provider boundary intact, and do not add a duplicate Meshy client.

## Local validation

```bash
uv sync --all-extras
uv run pytest
uv run pytest --cov=meshy_content_generator --cov-report=xml:coverage.xml
uv run ruff check .
uv run mypy src
uv build

pnpm install --frozen-lockfile
pnpm --dir docs run validate
pnpm --dir docs run check-generated
pre-commit run --all-files
```

Paid API tests are forbidden by default. Test pipelines through `--dry-run` or
`--fixture-image` and mock `vendor-fabric` at the adapter boundary.

Pull requests and `main` are also analyzed by SonarQube Cloud as part of the
same CI workflow. Its organization-managed GitHub credential is unavailable to
local contributors, who do not need a token for local validation.

## Change boundaries

- Keep provider HTTP, credentials, retries, polling, downloads, and vendor
  errors in `vendor-fabric`.
- Keep pipeline expansion and ImageMagick operations deterministic and covered
  by tests.
- Update the Sourcey pages and generated API reference for public API changes.
- Do not commit build output, credentials, cache directories, or fixture assets
  without a documented reason.
