---
title: Architecture
description: Ownership boundaries and deterministic execution model.
---

# Architecture

The pipeline is intentionally narrow:

```text
JSON catalogue + pipeline manifest
          │
          ▼
template + matrix expansion ──> validated PipelineItem plan
          │
          ├── dry run: JSON plan only
          └── execution
                  │
                  ├── vendor-fabric ImageGenerator (real raw image)
                  └── fixture image (credit-free raw image)
                          │
                          ▼
                  ordered ImageMagick operations
```

`vendor-fabric` is the sole Meshy integration boundary. It owns authentication,
HTTP, error translation, retries, polling, downloads, and resumable job state.
`meshy-content-generator` only renders declarative data and makes local
deterministic transformations. This separation prevents credential drift and
keeps local fixture tests free of paid API calls.

The runner skips completed final outputs unless `--force` is requested. Every
selected operation receives the expanded item variables, so conditional
post-processing is deterministic and inspectable from the manifest.
