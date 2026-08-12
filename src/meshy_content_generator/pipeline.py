"""Pipeline loading, expansion, provider dispatch, and local image processing."""

from __future__ import annotations

import itertools
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

TOKEN = re.compile(r"\{([^{}]+)\}")


class ImageProvider(Protocol):
    """Provider boundary used by the declarative runner."""

    def generate(self, item: PipelineItem, root: Path) -> None:
        """Generate one raw image and its resumable vendor manifest."""


@dataclass(frozen=True)
class PipelineItem:
    """One fully expanded generation request."""

    asset_id: str
    prompt: str
    model: str
    aspect_ratio: str
    raw_output: Path
    final_output: Path
    variables: dict[str, object]


@dataclass(frozen=True)
class Operation:
    """One deterministic post-processing operation."""

    name: str
    options: dict[str, object]
    when: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class Pipeline:
    """A validated, expanded declarative pipeline."""

    name: str
    root: Path
    items: tuple[PipelineItem, ...]
    operations: tuple[Operation, ...]
    continue_on_error: bool

    def select(self, ids: set[str] | None = None) -> tuple[PipelineItem, ...]:
        """Return all items or the requested asset IDs."""
        if not ids:
            return self.items
        selected = tuple(item for item in self.items if item.asset_id in ids)
        missing = ids.difference(item.asset_id for item in selected)
        if missing:
            msg = f"Unknown asset ids: {', '.join(sorted(missing))}"
            raise ValueError(msg)
        return selected

    def run(
        self,
        *,
        ids: set[str] | None = None,
        provider: ImageProvider | None = None,
        fixture_image: Path | None = None,
    ) -> list[Path]:
        """Generate and process selected items, or copy a fixture without network access."""
        if provider is None and fixture_image is None:
            provider = VendorFabricProvider()
        outputs: list[Path] = []
        failures: list[Exception] = []
        for item in self.select(ids):
            try:
                if item.final_output.exists():
                    outputs.append(item.final_output)
                    continue
                item.raw_output.parent.mkdir(parents=True, exist_ok=True)
                if not item.raw_output.exists():
                    if fixture_image is not None:
                        shutil.copyfile(fixture_image, item.raw_output)
                    else:
                        if provider is None:
                            msg = "A provider or fixture image is required"
                            raise RuntimeError(msg)
                        provider.generate(item, self.root)
                current = item.raw_output
                for operation in self.operations:
                    if _matches(operation, item.variables):
                        current = _process(current, operation)
                outputs.append(current)
            except Exception as error:
                if not self.continue_on_error:
                    raise
                failures.append(error)
        if failures:
            msg = f"{len(failures)} pipeline item(s) failed; first error: {failures[0]}"
            raise RuntimeError(msg) from failures[0]
        return outputs


class VendorFabricProvider:
    """Thin adapter to the canonical vendor-fabric Meshy job orchestration."""

    def generate(self, item: PipelineItem, root: Path) -> None:
        """Delegate all vendor behavior, including persistence, to vendor-fabric."""
        from vendor_fabric.meshy.jobs import ImageGenerator

        relative = item.raw_output.relative_to(root)
        ImageGenerator(output_root=str(root)).generate_image(
            item.prompt,
            output_path=str(relative),
            ai_model=item.model,
            aspect_ratio=item.aspect_ratio,
        )


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be an object")
    return cast("dict[str, Any]", value)


def _sequence(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be an array")
    return value


def _lookup(context: dict[str, object], expression: str) -> object:
    if expression.startswith("[") and expression.endswith("]"):
        dynamic = context.get(expression[1:-1])
        if not isinstance(dynamic, str):
            raise ValueError(f"Dynamic template key {expression} did not resolve to text")
        return context[dynamic]
    current: object = context
    for part in expression.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"Template value {{{expression}}} is missing")
        current = current[part]
    return current


def _render(template: object, context: dict[str, object]) -> str:
    if not isinstance(template, str):
        raise TypeError("Generation templates must be strings")

    def replace(match: re.Match[str]) -> str:
        expression, _, transform = match.group(1).partition("|")
        value = str(_lookup(context, expression))
        if transform == "upper":
            return value.upper()
        if transform:
            raise ValueError(f"Unknown template transform: {transform}")
        return value

    return TOKEN.sub(replace, template)


def load_pipeline(path: str | Path, *, root: str | Path | None = None) -> Pipeline:
    """Load and fully validate a pipeline and its prompt catalogue."""
    pipeline_path = Path(path).resolve()
    workspace = Path(root).resolve() if root else pipeline_path.parent
    data = _object(json.loads(pipeline_path.read_text()), "pipeline")
    if data.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    source_path = (workspace / str(data["source"])).resolve()
    source = _object(json.loads(source_path.read_text()), "source")
    record_keys = data["records"] if isinstance(data["records"], list) else [data["records"]]
    records = [record for key in record_keys for record in _sequence(source.get(str(key)), f"records.{key}")]
    generation = _object(data.get("generation"), "generation")
    max_prompt_length = int(str(generation.get("max_prompt_length", 0)))
    matrix_raw = _object(data.get("matrix", {}), "matrix")
    dimensions = [
        [(name, value) for value in _sequence(values, f"matrix.{name}")] for name, values in matrix_raw.items()
    ]
    combinations = itertools.product(*dimensions) if dimensions else [()]
    matrix_combinations = [dict(parts) for parts in combinations]
    items: list[PipelineItem] = []
    for raw_record in records:
        record = _object(raw_record, "record")
        for matrix in matrix_combinations:
            context: dict[str, object] = {**source, **record, **matrix}
            raw_output = workspace / _render(generation["output"], context)
            final_template = generation.get("final_output", generation["output"])
            prompt = _render(generation["prompt"], context)
            if max_prompt_length and len(prompt) > max_prompt_length:
                asset_id = _render(generation["id"], context)
                msg = f"Prompt for {asset_id} is {len(prompt)} characters; maximum is {max_prompt_length}"
                raise ValueError(msg)
            items.append(
                PipelineItem(
                    asset_id=_render(generation["id"], context),
                    prompt=prompt,
                    model=_render(generation["model"], context),
                    aspect_ratio=_render(generation["aspect_ratio"], context),
                    raw_output=raw_output,
                    final_output=workspace / _render(final_template, context),
                    variables=context,
                )
            )
    operations = tuple(_parse_operation(raw) for raw in _sequence(data.get("postprocess", []), "postprocess"))
    return Pipeline(
        name=str(data["name"]),
        root=workspace,
        items=tuple(items),
        operations=operations,
        continue_on_error=bool(data.get("continue_on_error", False)),
    )


def _parse_operation(raw: object) -> Operation:
    data = _object(raw, "operation")
    when_raw = _object(data.get("when", {}), "operation.when")
    when = {key: tuple(str(value) for value in _sequence(values, f"when.{key}")) for key, values in when_raw.items()}
    return Operation(str(data["op"]), {key: value for key, value in data.items() if key not in {"op", "when"}}, when)


def _matches(operation: Operation, variables: dict[str, object]) -> bool:
    return all(str(variables.get(key)) in accepted for key, accepted in operation.when.items())


def _magick(*arguments: str) -> None:
    subprocess.run(["magick", *arguments], check=True)


def _process(path: Path, operation: Operation) -> Path:
    options = operation.options
    if operation.name == "transparent":
        _magick(str(path), "-fuzz", str(options["fuzz"]), "-transparent", str(options.get("color", "white")), str(path))
    elif operation.name == "trim":
        if options.get("sample"):
            sample = str(options["sample"])
            color = subprocess.run(
                ["magick", str(path), "-format", f"%[pixel:p{{{sample}}}]", "info:"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            _magick(
                str(path),
                "-bordercolor",
                color,
                "-border",
                "1",
                "-fuzz",
                str(options.get("fuzz", "6%")),
                "-trim",
                "+repage",
                str(path),
            )
        else:
            _magick(str(path), "-trim", "+repage", str(path))
    elif operation.name == "square":
        _magick(
            str(path),
            "-background",
            "none",
            "-gravity",
            "center",
            "-extent",
            "%[fx:max(w,h)]x%[fx:max(w,h)]",
            str(path),
        )
    elif operation.name == "webp":
        destination = path.with_suffix(".webp")
        _magick(
            str(path),
            "-quality",
            str(options["quality"]),
            "-define",
            f"webp:alpha-quality={options['alpha_quality']}",
            str(destination),
        )
        if bool(options.get("delete_source", True)):
            path.unlink()
        return destination
    elif operation.name == "feather_edges":
        width = int(
            subprocess.run(
                ["magick", "identify", "-format", "%w", str(path)], check=True, capture_output=True, text=True
            ).stdout
        )
        height = int(
            subprocess.run(
                ["magick", "identify", "-format", "%h", str(path)], check=True, capture_output=True, text=True
            ).stdout
        )
        fade = max(width * int(str(options.get("percent", 7))) // 100, 6)
        inner = width - 2 * fade
        temporary = path.with_suffix(".tmp.webp")
        _magick(
            str(path),
            "(",
            "-size",
            f"{width}x{height}",
            "xc:black",
            "-fill",
            "white",
            "-draw",
            f"rectangle {fade},0 {fade + inner},{height}",
            "-blur",
            f"0x{fade // 2}",
            ")",
            "-alpha",
            "off",
            "-compose",
            "CopyOpacity",
            "-composite",
            "-quality",
            str(options["quality"]),
            "-define",
            f"webp:alpha-quality={options['alpha_quality']}",
            str(temporary),
        )
        temporary.replace(path)
    else:
        raise ValueError(f"Unknown postprocess operation: {operation.name}")
    return path
