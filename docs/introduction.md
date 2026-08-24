---
title: Introduction
description: Declarative, credit-aware Meshy image pipelines with deterministic local finishing.
---

# meshy-content-generator

`meshy-content-generator` turns a JSON prompt catalogue into an ordered image
generation plan and applies deterministic ImageMagick post-processing. It is a
small orchestration package, deliberately not another Meshy client.

It delegates provider work to [`vendor-fabric`](https://github.com/jbcom/vendor-fabric):
authentication, HTTP, retries, polling, downloads, vendor errors, and resumable
job sidecars all remain there. This package owns pipeline expansion, selection,
skip/force behavior, and local image transformations.

<CardGroup cols={2}>
  <Card title="Quick start" icon="rocket" href="/quickstart/">Install and run a credit-free plan preview.</Card>
  <Card title="Pipeline schema" icon="code" href="/pipeline-schema/">Author records, matrices, templates, and post-processing.</Card>
  <Card title="Library usage" icon="terminal" href="/library-usage/">Use the typed Python API or stable dry-run JSON in automation.</Card>
</CardGroup>

## Safety model

Every CLI invocation supports `--dry-run`. Dry runs validate and print the
fully resolved plan without importing the provider, reading credentials,
creating output directories, invoking ImageMagick, or making network requests.

For deterministic local verification, `--fixture-image` copies a supplied image
through the pipeline rather than submitting a paid generation request.

## Requirements

- Python 3.11 through 3.14
- [uv](https://docs.astral.sh/uv/) for development
- ImageMagick 7 (`magick`) only when executing post-processing
- a `vendor-fabric[meshy]` configuration only for real generation

The package itself does not read `MESHY_API_KEY`; provider configuration belongs
to `vendor-fabric`.
