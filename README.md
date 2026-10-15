# meshy-content-generator

<p align="center">
  <img src="https://raw.githubusercontent.com/jbcom/meshy-content-generator/main/docs/brand.svg" alt="meshy-content-generator declarative generation pipeline" width="760">
</p>

Declarative text-to-image and ImageMagick pipelines backed exclusively by
[`vendor-fabric`](https://github.com/jbcom/vendor-fabric). The package contains
no Meshy HTTP client, credential handling, retry loop, poller, or downloader.

[Documentation](https://jonbogaty.com/meshy-content-generator/) · [Quick start](https://jonbogaty.com/meshy-content-generator/quickstart/) · [Pipeline schema](https://jonbogaty.com/meshy-content-generator/pipeline-schema/) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md)

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
See [the architecture contract](https://jonbogaty.com/meshy-content-generator/architecture/).

Existing PNG artwork can use a source-hash-bound protection matte with
`content-gen cutout source.png output.png --annotations matte.json --dry-run`.
The cutout route requires ImageMagick even during validation, preserves native
dimensions and decoded RGB bytes, and never calls the generation provider.
See [protected cutouts](docs/protected-cutouts.md) for foreground polygons and
explicit seeds for enclosed background holes.
