---
title: Pipeline schema
description: JSON schema concepts for prompt catalogues, matrix expansion, templates, and ImageMagick operations.
---

# Pipeline schema

A pipeline points to a source JSON catalogue, selects one or more record arrays,
expands optional matrix dimensions, renders generation templates, and applies
declared post-processing operations in order.

```json
{
  "schema_version": 1,
  "name": "ducks",
  "source": "tools/prompts/ducks.json",
  "records": "items",
  "matrix": { "view": ["front", "side"] },
  "generation": {
    "id": "{id}-{view}",
    "prompt": "{prompt} {view|upper}",
    "model": "nano-banana-pro",
    "aspect_ratio": "1:1",
    "output": "public/art/{id}-{view}.png",
    "final_output": "public/art/{id}-{view}.webp"
  },
  "postprocess": [{ "op": "webp", "quality": 88, "alpha_quality": 95 }]
}
```

## Templates and matrices

Templates may read a record or source-root property (`{id}`, `{_style.model}`),
a matrix value (`{view}`), uppercase text (`{view|upper}`), or a dynamic key.
Dynamic keys work at the root (`{[layer]}`) and in nested mappings
(`{_style.coverage.[layer]}`). A missing value or unsupported transform fails
validation rather than silently producing a bad prompt.

`generation.max_prompt_length` may set a positive character limit. A plan whose
rendered prompt exceeds it fails before provider work begins.

## Output safety

All source, raw-output, and final-output paths resolve inside `--root`; path
traversal and symlink escapes fail validation. A pipeline may not overwrite its
own manifest or source catalogue. Expanded raw outputs and final outputs must
each be unique, and a raw output cannot be another asset's final output. This
prevents one generated image from being reused accidentally for a different
asset. A raw output may equal its own final output only when no conversion is
needed.

## Post-processing operations

Operations are executed in manifest order. `when` limits an operation to matrix
or source values:

```json
{ "op": "parallax_depth", "depth": "near", "when": { "layer": ["near"] } }
```

| Operation | Purpose |
| --- | --- |
| `transparent` | Key a color using ImageMagick fuzz. |
| `trim` | Trim transparent or sampled-color borders. |
| `square` | Center the image on a transparent square canvas. |
| `webp` | Encode WebP, optionally deleting the source. |
| `feather_edges` | Fade side edges while multiplying existing alpha. |
| `strip_painted_mat` | Remove full-height, low-variance painted side mats. |
| `parallax_depth` | Apply a deterministic radial alpha mask for `mid` or `near`. |

Mask operations preserve prior transparency by multiplying with existing alpha;
they cannot restore a keyed transparent pixel to opaque.
