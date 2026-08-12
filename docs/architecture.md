# Architecture

The package turns a JSON pipeline and a prompt catalogue into an ordered plan:

1. expand records and optional matrix variables;
2. render prompt, model, aspect ratio, and output templates;
3. submit through `vendor_fabric.meshy.jobs.ImageGenerator`;
4. run declared ImageMagick transformations in order.

The boundary is strict. `vendor-fabric` owns credentials, HTTP, rate limiting,
typed errors, polling, downloads, and resumable job sidecars. This package owns
only orchestration and local deterministic transformations. `--dry-run`
expands and validates the complete plan without importing the provider,
reading `MESHY_API_KEY`, touching outputs, or invoking ImageMagick.

Completed outputs are skipped by default. `--force` explicitly reruns a
selected item. Combined with `--fixture-image`, it can reprocess an existing
asset through a changed manifest without a provider import, network call, or
credit spend; without a fixture, forcing an item whose raw input is absent
requests a fresh generation.

## Pipeline schema

Each pipeline names a source JSON document, a record array, optional matrix
dimensions, generation templates, and post-processing operations. Templates
may read record or source-root fields (`{id}`, `{_style.model}`), matrix values
(`{layer}`), uppercase values (`{layer|upper}`), and a field selected by a
matrix value either at the root (`{[layer]}`) or below a nested object
(`{_style.coverage.[layer]}`). Supported operations are `transparent`, `trim`,
`square`, `webp`, `feather_edges`, `strip_painted_mat`, and
`parallax_depth`. Operations can be restricted with a simple `when` map, such
as `{ "layer": ["mid", "near"] }`.

`feather_edges`, `strip_painted_mat`, and `parallax_depth` multiply their masks
with the image's existing alpha. They cannot make a keyed transparent pixel
opaque again. `strip_painted_mat` detects full-height, low-variance edge bands
geometrically so shared highlight colours inside the artwork are preserved.
`parallax_depth` requires `depth` to be `mid` or `near`; use separate `when`
entries when a matrix expands both depths.

## Release order

The first standalone feature release depends on `vendor-fabric>=2.2.0,<3`, the
release that adds text-to-image. Publish vendor-fabric first, then this package,
then pin consumers to the released generator version.
