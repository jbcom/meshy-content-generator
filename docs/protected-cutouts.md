---
title: Protected PNG cutouts
description: Remove edge-connected checkerboards without erasing pale foreground art.
---

# Protected PNG cutouts

`content-gen cutout source.png output.png --annotations matte.json` processes an
existing PNG locally, without generation, credentials, resizing, trimming, or
color conversion. The output is lossless 8-bit RGBA PNG. Only alpha changes;
decoded RGB bytes remain identical, including pixels made transparent.
ImageMagick 7's `magick` executable is preferred. ImageMagick 6 installations
with both `convert` and `identify` are supported, including Ubuntu's packaged
tools. Full integration tests require one of these installations and fail
explicitly when the tools are missing rather than silently skipping PNG proof.

The connected-background rule accepts near-neutral pixels (channel spread at
most 16, mean brightness at least 72) reachable from an image edge. It then
removes connected light neutral fringe (spread at most 10, brightness at least
224). This is a candidate rule, not a universal foreground classifier. Authored
protected polygons stop both passes, including for pale paper, glass, and ink.
Enclosed holes require explicitly annotated background seeds. Original partial
alpha survives on retained pixels; this operation does not invent soft edges.

```json
{
  "schema_version": 1,
  "source_sha256": "the 64-character SHA-256 of source.png",
  "width": 1024,
  "height": 1024,
  "protected_polygons": [[[400, 200], [600, 200], [600, 800], [400, 800]]],
  "background_seeds": [[300, 300]]
}
```

Coordinates refer to the original pixel grid. Polygon vertices are canvas cell
corners, so coordinates may reach `width` and `height` at the outer boundary.
Polygons must have at least three integer vertices and nonzero area; a pixel is
protected when its center is inside a polygon. A seed must be an in-bounds
background candidate outside every protected polygon. Hash, size, geometry, or
seed mismatches fail before writing. Input, output, and annotation files must
be distinct. Existing outputs are refused unless `--force` is supplied.
`--dry-run` validates everything and prints the plan without writing files.

Keep original art and annotations under version control. Inspect the actual
output alpha and composite on light, dark, and saturated backgrounds before
admitting an asset. A few transparent pixels do not prove that all holes are
removed or all foreground retained. The Python buffer API accepts a full-size
protection mask for authoring workflows that already have one.
