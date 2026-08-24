---
title: Library usage
description: Use meshy-content-generator safely from Python and deterministic automation.
---

# Library usage

Use the package as a planner first. `load_pipeline` validates the manifest and
catalogue, expands records and matrices, resolves all paths beneath the
workspace root, and returns immutable `PipelineItem` values. No provider is
imported and no files are written while the plan is loaded or selected.

```python
from pathlib import Path

from meshy_content_generator import load_pipeline

root = Path(".").resolve()
pipeline = load_pipeline("tools/pipelines/ducks.json", root=root)
items = pipeline.select({"duck-front"})

for item in items:
    print(item.asset_id, item.prompt, item.final_output.relative_to(root))
```

## Choose an execution mode

| Need | API or command | Provider, credentials, and network |
| --- | --- | --- |
| Validate and inspect a plan | `load_pipeline()` and `Pipeline.select()` | Never used. |
| Give an agent machine-readable plan data | `content-gen run … --dry-run` | Never used; emits formatted JSON. |
| Verify ImageMagick operations locally | `pipeline.run(fixture_image=Path(...))` | Never used; the fixture is copied as raw input. |
| Generate real images | `pipeline.run()` | Delegated only to `vendor-fabric`. |

The command-line dry run is the best hand-off format for an agentic workflow:
it returns the pipeline name plus every selected item's ID, prompt, model,
aspect ratio, raw output, and final output. Treat that output as a reviewed
plan, not proof that an image was generated.

```bash
content-gen run tools/pipelines/ducks.json --root . --dry-run
```

## Run deterministic fixture processing

Fixture mode executes the same selection, skip/force, and post-processing path
as a live run, but never constructs `VendorFabricProvider`:

```python
outputs = pipeline.run(
    ids={"duck-front"},
    fixture_image=Path("tests/fixtures/duck.png"),
    force=True,
)
```

`force=True` is explicit: it rebuilds selected final outputs that would
otherwise be skipped. Keep fixture images local and non-sensitive; do not use
paid-generation output as a test fixture.

## Run real generation

For real work, omit `fixture_image`. The package creates its standard
`VendorFabricProvider` and delegates to `vendor-fabric` for authentication,
HTTP, retries, polling, downloads, vendor error mapping, and resumable job
state:

```python
outputs = pipeline.run(ids={"duck-front"})
```

Do not add a Meshy client, API key lookup, retry loop, or downloader around
this call. Configure the supported provider in `vendor-fabric`; this package
only supplies the resolved prompt, model, aspect ratio, and workspace-relative
raw output target.

## Inject a provider in an integration test

`Pipeline.run` accepts the small `ImageProvider` protocol when a caller needs
to test its own integration boundary. A provider receives the already-validated
item and root and must write the item's raw output. It should not change the
manifest, final-output path, or local post-processing contract.

```python
from pathlib import Path

from meshy_content_generator import PipelineItem, load_pipeline


class LocalProvider:
    def generate(self, item: PipelineItem, root: Path) -> None:
        item.raw_output.write_bytes(Path("tests/fixtures/duck.png").read_bytes())


pipeline = load_pipeline("tools/pipelines/ducks.json", root=".")
outputs = pipeline.run(ids={"duck-front"}, provider=LocalProvider())
```

Prefer `fixture_image` when it expresses the test; it is less code and proves
the credential-free route directly. Inject a provider only to test the
provider-facing seam. See [Architecture](/architecture/) for the ownership
boundary and [Pipeline schema](/pipeline-schema/) for the manifest contract.
