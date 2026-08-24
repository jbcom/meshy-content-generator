# Agent protocols

This is the standalone declarative Meshy pipeline package extracted from
`jbcom/agentic`. Work docs first, tests second, code last. The package owns
pipeline expansion and deterministic ImageMagick post-processing. It never
owns Meshy HTTP, authentication, retries, polling, downloads, or vendor error
translation; those belong exclusively to `vendor-fabric`.

Run `uv sync --all-extras`, `uv run pytest`, `uv run ruff check .`,
`uv run mypy src`, and `uv build`. Paid API tests are forbidden by default.
Every CLI route must support `--dry-run`, which must not require credentials or
make a network request.

## Documentation

Sourcey is the only documentation renderer. Authored pages and the Sourcey
configuration live in `docs/`; `docs/api-reference.md` is generated from public
Python source by `scripts/generate_api_docs.py` and must never be hand-edited.
Run `pnpm install --frozen-lockfile`, `pnpm --dir docs run validate`, and
`pnpm --dir docs run check-generated` with the locked docs toolchain. Sourcey
build output (`docs/dist/`) is untracked and generates the deployed site's
`llms.txt`, `llms-full.txt`, and sitemap; do not create a competing root
documentation-derived `llms.txt`.

## Delivery and collaboration

Use Conventional Commits and work on an upstream topic branch. Open a draft PR
while actively changing it; make it ready only when its complete validation
suite is green. Preserve history: update topic branches with `git merge main`
and merge PRs with merge commits only—never squash, rebase, force-push, or use
an administrative bypass.

`release-please` owns versions, tags, releases, and `CHANGELOG.md`. `cd.yml`
publishes a released tag through PyPI trusted publishing and deploys the Sourcey
site through GitHub Pages. Pull-request workflows never publish packages,
deploy docs, or receive release credentials. External forks are untrusted and
cannot modify control-plane workflows, release metadata, or Sourcey build
configuration.
