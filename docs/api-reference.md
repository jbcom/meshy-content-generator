---
title: Python API reference
description: Generated public API reference for meshy-content-generator.
---

# Python API reference

This file is generated from public classes, functions, signatures, and docstrings in `src/`.
Regenerate it with `pnpm --dir docs run generate-api`; CI rejects a stale result.

## `cli`

### `parser()`

Build the CLI parser.

### `main(argv: Sequence[str] | None=None)`

Run a declarative pipeline.

## `pipeline`

### `ImageProvider`

Provider boundary used by the declarative runner.

#### `generate(self, item: PipelineItem, root: Path)`

Generate one raw image and its resumable vendor manifest.

### `PipelineItem`

One fully expanded generation request.

### `Operation`

One deterministic post-processing operation.

### `Pipeline`

A validated, expanded declarative pipeline.

#### `select(self, ids: set[str] | None=None)`

Return all items or the requested asset IDs.

#### `run(self, *, ids: set[str] | None=None, provider: ImageProvider | None=None, fixture_image: Path | None=None, force: bool=False)`

Generate and process selected items, or copy a fixture without network access.

### `VendorFabricProvider`

Thin adapter to the canonical vendor-fabric Meshy job orchestration.

#### `generate(self, item: PipelineItem, root: Path)`

Delegate all vendor behavior, including persistence, to vendor-fabric.

### `load_pipeline(path: str | Path, *, root: str | Path | None=None)`

Load and fully validate a pipeline and its prompt catalogue.
