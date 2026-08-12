# meshy-content-generator

Declarative text-to-image and ImageMagick pipelines backed exclusively by
[`vendor-fabric`](https://github.com/jbcom/vendor-fabric). The package contains
no Meshy HTTP client, credential handling, retry loop, poller, or downloader.

```bash
uvx --from meshy-content-generator content-gen run tools/pipelines/ducks.json --root . --dry-run
uvx --from meshy-content-generator content-gen run tools/pipelines/ducks.json --root . soot-sparrow
```

`--dry-run` validates and prints every resolved request without credentials,
network access, output writes, or ImageMagick. `--fixture-image image.png`
exercises the full local post-processing pipeline without spending credits.
See [the architecture contract](docs/architecture.md).
