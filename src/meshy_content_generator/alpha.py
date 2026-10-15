"""Source-bound, protected removal of edge-connected neutral checkerboards."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import tempfile
from collections import deque
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from meshy_content_generator.pipeline import _magick_command

COORDINATE_DIMENSIONS = 2
MIN_POLYGON_VERTICES = 3
PNG_BITS = 8
RGBA_STREAM = "rgba:-"


def _candidate(pixels: bytes, index: int, *, fringe: bool = False) -> bool:
    red, green, blue, alpha = pixels[index * 4 : index * 4 + 4]
    if alpha == 0:
        return True
    spread, minimum_mean = (10, 224) if fringe else (16, 72)
    return max(red, green, blue) - min(red, green, blue) <= spread and red + green + blue >= minimum_mean * 3


def _point(value: object, width: int, height: int) -> tuple[int, int]:
    if (
        not isinstance(value, (list, tuple))
        or len(value) != COORDINATE_DIMENSIONS
        or any(type(coordinate) is not int for coordinate in value)
        or not 0 <= value[0] < width
        or not 0 <= value[1] < height
    ):
        raise ValueError("Coordinates must be in-bounds integer pairs")
    return value[0], value[1]


def _seed_indices(
    seeds: Sequence[tuple[int, int]],
    pixels: bytes,
    protection: bytes,
    width: int,
    height: int,
) -> list[int]:
    indices = []
    for seed in seeds:
        x, y = _point(seed, width, height)
        index = y * width + x
        if protection[index]:
            raise ValueError("A background seed cannot identify protected foreground")
        if not _candidate(pixels, index):
            raise ValueError("A seed must identify a neutral background candidate")
        indices.append(index)
    return indices


class _BackgroundFlood:
    def __init__(self, pixels: bytes, width: int, height: int, protection: bytes) -> None:
        """Keep both connected-background passes on one native pixel grid."""
        self.pixels, self.width, self.height, self.protection = pixels, width, height, protection
        self.removed = bytearray(width * height)
        self.visited = bytearray(width * height)
        self.queue: deque[int] = deque()

    def enqueue(self, index: int, *, fringe: bool = False) -> None:
        """Queue only unprotected, previously unvisited candidate pixels."""
        if self.visited[index] or self.protection[index]:
            return
        self.visited[index] = 1
        if _candidate(self.pixels, index, fringe=fringe):
            self.removed[index] = 1
            self.queue.append(index)

    def neighbors(self, index: int) -> list[int]:
        """Return four-connected neighbors without wrapping row boundaries."""
        x, y = index % self.width, index // self.width
        neighbors = []
        if x:
            neighbors.append(index - 1)
        if x + 1 < self.width:
            neighbors.append(index + 1)
        if y:
            neighbors.append(index - self.width)
        if y + 1 < self.height:
            neighbors.append(index + self.width)
        return neighbors

    def grow(self, *, fringe: bool = False) -> None:
        """Visit candidates connected to the current roots."""
        while self.queue:
            for index in self.neighbors(self.queue.popleft()):
                self.enqueue(index, fringe=fringe)

    def start_fringe(self) -> None:
        """Use removed pixels and existing transparency as fringe roots."""
        self.visited = bytearray(self.width * self.height)
        for index, removed in enumerate(self.removed):
            if removed or self.pixels[index * 4 + 3] == 0:
                self.visited[index] = 1
                self.queue.append(index)


def remove_checkerboard_background(
    pixels: bytes,
    width: int,
    height: int,
    *,
    protected_mask: bytes | None = None,
    background_seeds: Sequence[tuple[int, int]] = (),
) -> bytes:
    """Remove neutral edge-connected background and explicitly seeded enclosed holes.

    Accept tightly packed 8-bit RGBA bytes. Nonzero protection-mask entries
    preserve the corresponding source pixel exactly, including partial alpha.
    RGB bytes, buffer length, and retained alpha are never changed. Neutral
    light fringe grows only through unprotected pixels. Seeds must identify
    neutral background, never protected foreground. This is a conservative
    candidate rule; callers author protection for pale or neutral subjects.
    """
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise ValueError("Dimensions must be positive integers")
    count = width * height
    if len(pixels) != count * 4:
        raise ValueError("RGBA buffer length does not match dimensions")
    if protected_mask is not None and len(protected_mask) != count:
        raise ValueError("The protection mask must contain one byte per pixel")
    protection = protected_mask if protected_mask is not None else bytes(count)
    seed_indices = _seed_indices(background_seeds, pixels, protection, width, height)
    flood = _BackgroundFlood(pixels, width, height, protection)
    for x in range(width):
        flood.enqueue(x)
        flood.enqueue((height - 1) * width + x)
    for y in range(1, height - 1):
        flood.enqueue(y * width)
        flood.enqueue(y * width + width - 1)
    for index in seed_indices:
        flood.enqueue(index)
    flood.grow()
    flood.start_fringe()
    flood.grow(fringe=True)
    output = bytearray(pixels)
    for index, remove in enumerate(flood.removed):
        if remove:
            output[index * 4 + 3] = 0
    return bytes(output)


def _polygon(raw_polygon: object, width: int, height: int) -> list[tuple[int, int]]:
    if not isinstance(raw_polygon, list) or len(raw_polygon) < MIN_POLYGON_VERTICES:
        raise ValueError("Protected polygons need at least three vertices")
    polygon = [_point(point, width + 1, height + 1) for point in raw_polygon]
    edges = zip(polygon, [*polygon[1:], polygon[0]], strict=True)
    if not sum(start[0] * end[1] - end[0] * start[1] for start, end in edges):
        raise ValueError("Protected polygons must have nonzero area")
    return polygon


def _row_spans(polygon: list[tuple[int, int]], y: int) -> list[tuple[int, int]]:
    scan, intersections = y + 0.5, []
    for start, end in zip(polygon, [*polygon[1:], polygon[0]], strict=True):
        if min(start[1], end[1]) <= scan < max(start[1], end[1]):
            intersections.append(start[0] + (scan - start[1]) * (end[0] - start[0]) / (end[1] - start[1]))
    intersections.sort()
    return [
        (math.ceil(left - 0.5), math.ceil(right - 0.5))
        for left, right in zip(intersections[::2], intersections[1::2], strict=True)
    ]


def _protection_mask(polygons: object, width: int, height: int) -> bytes:
    if not isinstance(polygons, list):
        raise TypeError("protected_polygons must be an array")
    mask = bytearray(width * height)
    for raw_polygon in polygons:
        polygon = _polygon(raw_polygon, width, height)
        for y in range(min(point[1] for point in polygon), max(point[1] for point in polygon)):
            for first, last in _row_spans(polygon, y):
                mask[y * width + first : y * width + last] = b"\1" * (last - first)
    return bytes(mask)


def _source_annotation(source: Path, annotations: Path) -> tuple[dict[str, object], str]:
    raw_annotation: object = json.loads(annotations.read_text(encoding="utf-8"))
    if not isinstance(raw_annotation, dict) or raw_annotation.get("schema_version") != 1:
        raise ValueError("Annotations require schema_version 1")
    data = cast("dict[str, object]", raw_annotation)
    source_bytes = source.read_bytes()
    if not source_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Source must be a PNG image")
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    if source_hash != data.get("source_sha256"):
        raise ValueError("Annotation source hash does not match the source PNG")
    return data, source_hash


def _source_dimensions(source: Path, data: dict[str, object]) -> tuple[int, int]:
    dimensions = subprocess.run(
        [*_magick_command("identify"), "-format", "%w %h %z", str(source)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    if len(dimensions) != len(("width", "height", "depth")):
        raise ValueError("Source must contain exactly one PNG image")
    width, height, depth = (int(value) for value in dimensions)
    if depth != PNG_BITS:
        raise ValueError("Protected cutouts require 8-bit source pixels")
    if width != data.get("width") or height != data.get("height"):
        raise ValueError("Annotation dimensions do not match source PNG")
    return width, height


def cutout_png(
    source: Path,
    output: Path,
    annotations: Path,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, object]:
    """Write a lossless source-bound PNG cutout, or validate its offline plan.

    Annotation JSON contains schema_version=1, source_sha256, width, height,
    protected_polygons, and background_seeds. ImageMagick must be installed.
    Input files remain untouched. Existing output requires force=True.
    """
    source, output, annotations = source.resolve(), output.resolve(), annotations.resolve()
    if source in (output, annotations) or output == annotations:
        raise ValueError("Source, output, and annotations must be distinct")
    if source.suffix.lower() != ".png" or output.suffix.lower() != ".png":
        raise ValueError("Protected cutouts require PNG source and output")
    if output.exists() and not force:
        raise FileExistsError(output)
    data, source_hash = _source_annotation(source, annotations)
    width, height = _source_dimensions(source, data)
    protection = _protection_mask(data.get("protected_polygons"), width, height)
    raw_seeds = data.get("background_seeds")
    if not isinstance(raw_seeds, list):
        raise TypeError("background_seeds must be an array")
    seeds = tuple(_point(value, width, height) for value in raw_seeds)
    pixels = subprocess.run(
        [*_magick_command(), str(source), "-depth", "8", RGBA_STREAM],
        check=True,
        capture_output=True,
    ).stdout
    result = remove_checkerboard_background(pixels, width, height, protected_mask=protection, background_seeds=seeds)
    plan: dict[str, object] = {
        "source_sha256": source_hash,
        "width": width,
        "height": height,
        "protected_pixels": sum(bool(value) for value in protection),
        "transparent_pixels": result[3::4].count(0),
        "output": str(output),
    }
    if not dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        _write_png(output, width, height, result)
        plan["output_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    return plan


def _write_png(output: Path, width: int, height: int, pixels: bytes) -> None:
    with tempfile.TemporaryDirectory(prefix=".cutout-", dir=output.parent) as directory:
        temporary = Path(directory) / output.name
        subprocess.run(
            [
                *_magick_command(),
                "-size",
                f"{width}x{height}",
                "-depth",
                "8",
                RGBA_STREAM,
                "-define",
                "png:color-type=6",
                "-define",
                "png:exclude-chunks=date,time",
                str(temporary),
            ],
            input=pixels,
            check=True,
            capture_output=True,
        )
        decoded = subprocess.run(
            [*_magick_command(), str(temporary), "-depth", "8", RGBA_STREAM],
            check=True,
            capture_output=True,
        ).stdout
        if decoded != pixels:
            raise ValueError("PNG encoding changed decoded pixel bytes; output was not written")
        temporary.replace(output)
