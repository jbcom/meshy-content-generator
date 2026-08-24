---
title: Quick start
description: Install the package, preview a plan without credentials, then run deterministic fixture processing.
---

# Quick start

Install the command with your preferred Python environment manager:

```bash
uv tool install meshy-content-generator
```

Preview a pipeline first. This route is safe for CI and does not spend credits:

```bash
content-gen run tools/pipelines/ducks.json --root . --dry-run
```

The JSON output shows the expanded asset IDs, prompts, model, aspect ratio, raw
output, and final output. Limit work to known assets by supplying IDs after the
pipeline path:

```bash
content-gen run tools/pipelines/ducks.json --root . duck-front --dry-run
```

## Test post-processing without a provider

Use an existing image as a fixture to exercise the local operations without
credentials or network access:

```bash
content-gen run tools/pipelines/backdrops.json \
  --root . scene-near --force --fixture-image public/art/backdrops/scene-near.webp
```

Completed final outputs are skipped by default. `--force` explicitly reruns the
selected item. With a fixture it rebuilds the raw input from that fixture; with
no fixture it asks `vendor-fabric` for a fresh generation if the raw input is
absent.

> [!NOTE]
> Real generation is intentionally delegated to `vendor-fabric`. Configure its
> supported provider authentication there; this package never implements a
> second HTTP or credential layer.
