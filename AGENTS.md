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

