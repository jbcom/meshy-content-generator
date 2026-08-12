import ast
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from meshy_content_generator.cli import main
from meshy_content_generator.pipeline import VendorFabricProvider, load_pipeline


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


def test_unknown_id_and_operation_fail_closed(tmp_path: Path) -> None:
    pipeline = load_pipeline(write_pipeline(tmp_path), root=tmp_path)
    with pytest.raises(ValueError, match="Unknown asset ids"):
        pipeline.select({"missing"})
    invalid = load_pipeline(write_pipeline(tmp_path, postprocess=[{"op": "unknown"}]), root=tmp_path)
    fixture = tmp_path / "fixture.png"
    fixture.write_bytes(b"not needed")
    with pytest.raises(ValueError, match="Unknown postprocess operation"):
        invalid.run(ids={"duck-front"}, fixture_image=fixture)
