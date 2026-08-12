"""Command-line interface for declarative image pipelines."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from meshy_content_generator.pipeline import load_pipeline


def parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    command = argparse.ArgumentParser(prog="content-gen")
    subcommands = command.add_subparsers(dest="command", required=True)
    run = subcommands.add_parser("run")
    run.add_argument("pipeline", type=Path)
    run.add_argument("ids", nargs="*")
    run.add_argument("--root", type=Path, default=Path.cwd())
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--fixture-image", type=Path)
    run.add_argument("--force", action="store_true")
    return command


def main(argv: Sequence[str] | None = None) -> int:
    """Run a declarative pipeline."""
    arguments = parser().parse_args(argv)
    pipeline = load_pipeline(arguments.pipeline, root=arguments.root)
    ids = set(arguments.ids) or None
    if arguments.dry_run:
        plan = [
            {
                "id": item.asset_id,
                "prompt": item.prompt,
                "model": item.model,
                "aspect_ratio": item.aspect_ratio,
                "raw_output": str(item.raw_output.relative_to(pipeline.root)),
                "final_output": str(item.final_output.relative_to(pipeline.root)),
            }
            for item in pipeline.select(ids)
        ]
        print(json.dumps({"pipeline": pipeline.name, "items": plan}, indent=2))
        return 0
    outputs = pipeline.run(ids=ids, fixture_image=arguments.fixture_image, force=arguments.force)
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
