import ast
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from meshy_content_generator.cli import main
from meshy_content_generator.pipeline import Operation, VendorFabricProvider, _process, load_pipeline


def write_pipeline(root: Path, *, postprocess: list[dict[str, object]] | None = None) -> Path:
    (root / "catalogue.json").write_text(
        json.dumps(
            {
                "_style": {"model": "nano-banana-pro", "aspect": "1:1", "shared": "pure white"},
                "items": [{"id": "duck", "prompt": "a duck"}],
            }
        )
    )
    pipeline = root / "pipeline.json"
    pipeline.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "name": "fixture",
                "source": "catalogue.json",
                "records": "items",
                "generation": {
                    "id": "{id}-{view}",
                    "prompt": "{prompt} {_style.shared} {view|upper}",
                    "model": "{_style.model}",
                    "aspect_ratio": "{_style.aspect}",
                    "output": "out/{id}-{view}.png",
                    "final_output": "out/{id}-{view}.webp",
                },
                "matrix": {"view": ["front", "side"]},
                "postprocess": postprocess or [],
            }
        )
    )
    return pipeline


def test_pipeline_expands_matrix_templates_and_dry_run_has_no_provider_import(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pipeline = write_pipeline(tmp_path)
    with patch("meshy_content_generator.pipeline.VendorFabricProvider") as provider:
        assert main(["run", str(pipeline), "--root", str(tmp_path), "--dry-run"]) == 0
    provider.assert_not_called()
    payload = json.loads(capsys.readouterr().out)
    assert [item["id"] for item in payload["items"]] == ["duck-front", "duck-side"]
    assert payload["items"][1]["prompt"] == "a duck pure white SIDE"
    assert not (tmp_path / "out").exists()


def test_vendor_adapter_delegates_job_persistence_polling_and_download(tmp_path: Path) -> None:
    item = load_pipeline(write_pipeline(tmp_path), root=tmp_path).items[0]
    generator = MagicMock()
    with patch("vendor_fabric.meshy.jobs.ImageGenerator", return_value=generator) as image_generator:
        VendorFabricProvider().generate(item, tmp_path)
    image_generator.assert_called_once_with(output_root=str(tmp_path))
    generator.generate_image.assert_called_once_with(
        "a duck pure white FRONT",
        output_path="out/duck-front.png",
        ai_model="nano-banana-pro",
        aspect_ratio="1:1",
    )


def test_runtime_contains_no_duplicate_network_client() -> None:
    source_root = Path(__file__).parents[1] / "src" / "meshy_content_generator"
    forbidden = {"httpx", "requests", "urllib", "aiohttp"}
    imported: set[str] = set()
    for source_path in source_root.glob("*.py"):
        tree = ast.parse(source_path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(forbidden)
    provider_source = (source_root / "pipeline.py").read_text()
    assert "from vendor_fabric.meshy.jobs import ImageGenerator" in provider_source
    assert "MESHY_API_KEY" not in provider_source


def test_fixture_mode_processes_without_provider(tmp_path: Path) -> None:
    if not __import__("shutil").which("magick"):
        pytest.skip("ImageMagick unavailable")
    fixture = tmp_path / "fixture.png"
    subprocess.run(["magick", "-size", "8x4", "xc:white", str(fixture)], check=True)
    pipeline = load_pipeline(
        write_pipeline(
            tmp_path,
            postprocess=[
                {"op": "transparent", "fuzz": "12%", "color": "white"},
                {"op": "square"},
                {"op": "webp", "quality": 88, "alpha_quality": 95},
            ],
        ),
        root=tmp_path,
    )
    with patch("meshy_content_generator.pipeline.VendorFabricProvider") as provider:
        outputs = pipeline.run(fixture_image=fixture)
    provider.assert_not_called()
    assert len(outputs) == 2
    assert all(output.suffix == ".webp" and output.exists() for output in outputs)
    assert not any((tmp_path / "out").glob("*.png"))


def test_force_reprocesses_existing_output_from_fixture_without_provider(tmp_path: Path) -> None:
    if not __import__("shutil").which("magick"):
        pytest.skip("ImageMagick unavailable")
    fixture = tmp_path / "fixture.webp"
    subprocess.run(["magick", "-size", "8x4", "xc:black", str(fixture)], check=True)
    pipeline_path = write_pipeline(
        tmp_path,
        postprocess=[{"op": "webp", "quality": 88, "alpha_quality": 95}],
    )
    existing = tmp_path / "out" / "duck-front.webp"
    existing.parent.mkdir(parents=True)
    subprocess.run(["magick", "-size", "2x2", "xc:white", str(existing)], check=True)

    with patch("meshy_content_generator.pipeline.VendorFabricProvider") as provider:
        assert main(
            [
                "run",
                str(pipeline_path),
                "--root",
                str(tmp_path),
                "duck-front",
                "--force",
                "--fixture-image",
                str(fixture),
            ]
        ) == 0
    provider.assert_not_called()
    dimensions = subprocess.run(
        ["magick", "identify", "-format", "%wx%h", str(existing)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert dimensions == "8x4"


def test_dynamic_nested_template_key_selects_depth_prompt(tmp_path: Path) -> None:
    source = tmp_path / "prompts.json"
    source.write_text(
        json.dumps(
            {
                "coverage": {"far": "full", "near": "edge-only"},
                "records": [{"id": "scene", "far": "sky", "near": "branches"}],
            }
        )
    )
    manifest = json.loads(write_pipeline(tmp_path).read_text())
    manifest["source"] = "prompts.json"
    manifest["records"] = "records"
    manifest["matrix"] = {"layer": ["far", "near"]}
    manifest["generation"]["id"] = "{id}-{layer}"
    manifest["generation"]["prompt"] = "{coverage.[layer]} {[layer]}"
    manifest["generation"]["model"] = "model"
    manifest["generation"]["aspect_ratio"] = "1:1"
    manifest["generation"]["output"] = "out/{id}-{layer}.png"
    manifest["generation"]["final_output"] = "out/{id}-{layer}.webp"
    path = tmp_path / "pipeline.json"
    path.write_text(json.dumps(manifest))

    pipeline = load_pipeline(path, root=tmp_path)
    assert [item.prompt for item in pipeline.items] == ["full sky", "edge-only branches"]


def test_feather_multiplies_existing_alpha_instead_of_restoring_it(tmp_path: Path) -> None:
    if not __import__("shutil").which("magick"):
        pytest.skip("ImageMagick unavailable")
    image = tmp_path / "alpha.webp"
    subprocess.run(
        [
            "magick",
            "-size",
            "40x20",
            "xc:none",
            "-fill",
            "white",
            "-draw",
            "rectangle 0,0 15,19 rectangle 24,0 39,19",
            "-define",
            "webp:lossless=true",
            str(image),
        ],
        check=True,
    )
    _process(
        image,
        Operation("feather_edges", {"percent": 10, "quality": 100, "alpha_quality": 100}, {}),
    )
    centre_alpha = subprocess.run(
        ["magick", str(image), "-format", "%[fx:p{20,10}.a]", "info:"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert float(centre_alpha) < 0.05


def test_strip_mat_and_depth_masks_are_deterministic(tmp_path: Path) -> None:
    if not __import__("shutil").which("magick"):
        pytest.skip("ImageMagick unavailable")
    image = tmp_path / "scene.webp"
    subprocess.run(
        [
            "magick",
            "-size",
            "60x40",
            "xc:gray70",
            "-fill",
            "black",
            "-draw",
            "rectangle 20,0 39,39",
            "-fill",
            "white",
            "-draw",
            "circle 30,20 34,20",
            str(image),
        ],
        check=True,
    )
    _process(image, Operation("strip_painted_mat", {"flat_sd": 12, "step": 4, "soften": 1}, {}))
    margin_alpha = subprocess.run(
        ["magick", str(image), "-format", "%[fx:p{4,20}.a]", "info:"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert float(margin_alpha) < 0.05

    _process(image, Operation("parallax_depth", {"depth": "near"}, {}))
    alpha = subprocess.run(
        ["magick", str(image), "-format", "%[fx:p{30,20}.a],%[fx:p{39,20}.a]", "info:"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    centre, edge = (float(value) for value in alpha.split(","))
    assert centre < edge


def test_parallax_depth_rejects_unknown_depth_before_processing(tmp_path: Path) -> None:
    image = tmp_path / "scene.webp"
    image.write_bytes(b"not processed")
    with pytest.raises(ValueError, match="depth must be 'mid' or 'near'"):
        _process(image, Operation("parallax_depth", {"depth": "far"}, {}))


def test_strip_painted_mat_rejects_non_positive_scan_step(tmp_path: Path) -> None:
    if not __import__("shutil").which("magick"):
        pytest.skip("ImageMagick unavailable")
    image = tmp_path / "scene.webp"
    subprocess.run(["magick", "-size", "40x40", "xc:white", str(image)], check=True)
    with pytest.raises(ValueError, match="step must be positive"):
        _process(image, Operation("strip_painted_mat", {"step": 0}, {}))


def test_unknown_id_and_operation_fail_closed(tmp_path: Path) -> None:
    pipeline = load_pipeline(write_pipeline(tmp_path), root=tmp_path)
    with pytest.raises(ValueError, match="Unknown asset ids"):
        pipeline.select({"missing"})
    with pytest.raises(ValueError, match="Unknown postprocess operation"):
        load_pipeline(write_pipeline(tmp_path, postprocess=[{"op": "unknown"}]), root=tmp_path)


def test_pipeline_rejects_traversal_collisions_and_unknown_when_variables(tmp_path: Path) -> None:
    manifest_path = write_pipeline(tmp_path)
    manifest = json.loads(manifest_path.read_text())

    manifest["generation"]["output"] = "../outside.png"
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match=r"generation\.output must stay within"):
        load_pipeline(manifest_path, root=tmp_path)

    manifest["generation"]["output"] = "out/{id}.png"
    manifest["generation"]["final_output"] = "out/{id}.webp"
    manifest["postprocess"] = [{"op": "webp", "quality": 88, "alpha_quality": 95}]
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="duplicate final outputs"):
        load_pipeline(manifest_path, root=tmp_path)

    manifest["generation"]["id"] = "{id}"
    manifest["generation"]["final_output"] = "out/{id}-{view}.webp"
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="duplicate asset IDs"):
        load_pipeline(manifest_path, root=tmp_path)

    manifest["generation"]["id"] = "{id}-{view}"
    manifest["postprocess"] = [{"op": "webp", "quality": 88, "alpha_quality": 95, "when": {"typo": ["x"]}}]
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="unknown when variable"):
        load_pipeline(manifest_path, root=tmp_path)


def test_pipeline_rejects_incomplete_postprocess_and_empty_matrix_dimensions(tmp_path: Path) -> None:
    manifest_path = write_pipeline(tmp_path, postprocess=[{"op": "webp", "quality": 88}])
    with pytest.raises(ValueError, match="missing required option"):
        load_pipeline(manifest_path, root=tmp_path)

    manifest = json.loads(manifest_path.read_text())
    manifest["postprocess"] = []
    manifest["matrix"] = {"view": []}
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match=r"matrix\.view must not be empty"):
        load_pipeline(manifest_path, root=tmp_path)
