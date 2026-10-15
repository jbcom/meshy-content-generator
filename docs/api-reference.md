---
title: Python API reference
description: Generated public API reference for meshy-content-generator.
---

# Python API reference

This file is generated from public classes, functions, signatures, and docstrings in `src/`.
Regenerate it with `pnpm --dir docs run generate-api`; CI rejects a stale result.

## `alpha`

### `remove_checkerboard_background(pixels: bytes, width: int, height: int, *, protected_mask: bytes | None=None, background_seeds: Sequence[tuple[int, int]]=())`

Remove neutral edge-connected background and explicitly seeded enclosed holes.

Accept tightly packed 8-bit RGBA bytes. Nonzero protection-mask entries
preserve the corresponding source pixel exactly, including partial alpha.
RGB bytes, buffer length, and retained alpha are never changed. Neutral
light fringe grows only through unprotected pixels. Seeds must identify
neutral background, never protected foreground. This is a conservative
candidate rule; callers author protection for pale or neutral subjects.

### `cutout_png(source: Path, output: Path, annotations: Path, *, dry_run: bool=False, force: bool=False)`

Write a lossless source-bound PNG cutout, or validate its offline plan.

Annotation JSON contains schema_version=1, source_sha256, width, height,
protected_polygons, and background_seeds. ImageMagick must be installed.
Input files remain untouched. Existing output requires force=True.

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
