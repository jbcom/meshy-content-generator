---
title: CLI reference
description: Reference for the content-gen command and its safe execution modes.
---

# CLI reference

```text
content-gen run PIPELINE [IDS ...] [--root PATH] [--dry-run]
                [--fixture-image PATH] [--force]
```

| Argument | Meaning |
| --- | --- |
| `PIPELINE` | JSON pipeline manifest. |
| `IDS` | Optional expanded asset IDs. Unknown IDs fail closed. |
| `--root` | Workspace root used to resolve source and output paths. Defaults to the current directory. |
| `--dry-run` | Print the resolved plan only; never needs credentials, network, outputs, or ImageMagick. |
| `--fixture-image` | Copy a local image as raw input, avoiding provider work. |
| `--force` | Reprocess an existing selected final output. |

The command prints produced output paths for an execution and formatted JSON for
a dry run. Non-zero exits preserve provider and ImageMagick failures unless a
pipeline opts into `continue_on_error`, in which case the command reports an
aggregate failure after attempting remaining items.

For existing 8-bit PNG artwork, the local cutout route prints a JSON report:

```text
content-gen cutout SOURCE.png OUTPUT.png --annotations MATTE.json [--dry-run] [--force]
```

This route requires ImageMagick during both validation and execution, but never
requires credentials or network access. It validates source hashes, protection
polygons, and background seeds; `--dry-run` writes nothing. `--force` permits
replacing an existing destination. Expected validation and processing errors
return status 2, with a concise message on stderr and no JSON on stdout.
See [protected PNG cutouts](protected-cutouts.md) for the annotation contract.
