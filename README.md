# meshy-content-generator

Declarative text-to-image and ImageMagick pipelines backed exclusively by
[`vendor-fabric`](https://github.com/jbcom/vendor-fabric). The package contains
no Meshy HTTP client, credential handling, retry loop, poller, or downloader.

```bash
uvx --from meshy-content-generator content-gen run tools/pipelines/ducks.json --root . --dry-run
uvx --from meshy-content-generator content-gen run tools/pipelines/ducks.json --root . soot-sparrow
uvx --from meshy-content-generator content-gen run tools/pipelines/backdrops.json --root . scene-near --force --fixture-image public/art/backdrops/scene-near.webp
```

`--dry-run` validates and prints every resolved request without credentials,
network access, output writes, or ImageMagick. `--fixture-image image.png`
exercises the full local post-processing pipeline without spending credits.
Post-processing is manifest-owned, including alpha-preserving edge feathering,
painted-mat removal, and mid/near parallax depth masks.
See [the architecture contract](docs/architecture.md).
