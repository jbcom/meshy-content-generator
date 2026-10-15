import hashlib
import json
import subprocess

import pytest

from meshy_content_generator.alpha import _protection_mask, cutout_png, remove_checkerboard_background
from meshy_content_generator.cli import main
from meshy_content_generator.pipeline import _magick_command


def fixture_pixels():
    # A dark ring separates an enclosed neutral void from the border.
    pixels = bytearray([210, 210, 210, 255] * 49)
    for y in range(1, 6):
        for x in range(1, 6):
            pixels[(y * 7 + x) * 4 : (y * 7 + x + 1) * 4] = bytes([20, 30, 40, 255])
    pixels[(3 * 7 + 3) * 4 : (3 * 7 + 4) * 4] = bytes([240, 240, 240, 255])
    # Pale edge-connected foreground and a pre-existing antialiased edge.
    pixels[0:4] = bytes([248, 248, 248, 123])
    return bytes(pixels)


def test_connected_background_and_enclosed_seeds_preserve_every_rgb_byte():
    source = fixture_pixels()
    protection = bytes([1] + [0] * 48)
    output = remove_checkerboard_background(source, 7, 7, protected_mask=protection, background_seeds=((3, 3),))
    assert source == fixture_pixels()
    assert len(output) == len(source)
    assert output[0:4] == source[0:4]
    assert output[(3 * 7 + 3) * 4 + 3] == 0
    assert output[4 + 3] == 0
    assert output[(2 * 7 + 2) * 4 + 3] == 255
    assert output[0::4] == source[0::4]
    assert output[1::4] == source[1::4]
    assert output[2::4] == source[2::4]


def test_enclosed_neutral_subject_survives_without_explicit_seed():
    source = fixture_pixels()
    output = remove_checkerboard_background(source, 7, 7, protected_mask=bytes([1] + [0] * 48))
    assert output[(3 * 7 + 3) * 4 + 3] == 255


def test_fringe_pass_cannot_erase_protected_pale_subject_or_restore_prior_alpha():
    source = bytes([20, 30, 40, 0, 250, 250, 250, 91, 240, 240, 240, 63])
    output = remove_checkerboard_background(source, 3, 1, protected_mask=bytes([0, 1, 0]))
    assert output == bytes([20, 30, 40, 0, 250, 250, 250, 91, 240, 240, 240, 0])


def test_polygon_canvas_edges_can_protect_the_last_pixel_and_degenerate_regions_fail():
    assert _protection_mask([[[0, 0], [7, 0], [7, 7], [0, 7]]], 7, 7) == bytes([1] * 49)
    with pytest.raises(ValueError, match="nonzero area"):
        _protection_mask([[[0, 0], [1, 1], [2, 2]]], 7, 7)


@pytest.mark.parametrize(
    ("width", "height", "mask", "seeds", "message"),
    [
        (0, 7, None, (), "positive"),
        (7, 6, None, (), "RGBA buffer"),
        (7, 7, b"", (), "protection mask"),
        (7, 7, None, ((7, 0),), "in-bounds"),
        (7, 7, bytes([1] * 49), ((0, 0),), "protected"),
        (7, 7, None, ((1, 1),), "background candidate"),
    ],
)
def test_invalid_inputs_fail_closed(width, height, mask, seeds, message):
    source = fixture_pixels()
    with pytest.raises(ValueError, match=message):
        remove_checkerboard_background(source, width, height, protected_mask=mask, background_seeds=seeds)


@pytest.fixture
def png_source(tmp_path):
    source = tmp_path / "source.png"
    subprocess.run(
        [*_magick_command(), "-size", "7x7", "-depth", "8", "rgba:-", "-define", "png:color-type=6", str(source)],
        input=fixture_pixels(),
        check=True,
    )
    annotations = tmp_path / "matte.json"
    annotations.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "width": 7,
                "height": 7,
                "protected_polygons": [[[0, 0], [1, 0], [1, 1], [0, 1]]],
                "background_seeds": [[3, 3]],
            }
        )
    )
    return source, annotations


def test_png_cli_is_lossless_repeatable_offline_and_dry_run_writes_nothing(png_source, tmp_path, capsys):
    source, annotations = png_source
    output = tmp_path / "output.png"
    arguments = ["cutout", str(source), str(output), "--annotations", str(annotations)]
    assert main([*arguments, "--dry-run"]) == 0
    assert not output.exists()
    assert json.loads(capsys.readouterr().out)["width"] == 7
    assert main(arguments) == 0
    first = output.read_bytes()
    assert main([*arguments, "--force"]) == 0
    assert output.read_bytes() == first
    decoded = subprocess.run(
        [*_magick_command(), str(output), "-depth", "8", "rgba:-"],
        check=True,
        capture_output=True,
    ).stdout
    assert decoded == remove_checkerboard_background(
        fixture_pixels(),
        7,
        7,
        protected_mask=bytes([1] + [0] * 48),
        background_seeds=((3, 3),),
    )


def test_annotation_hash_dimensions_geometry_and_aliases_fail_before_write(png_source, tmp_path):
    source, annotations = png_source
    original = json.loads(annotations.read_text())
    output = tmp_path / "output.png"
    for field, value, message in [
        ("source_sha256", "0" * 64, "source hash"),
        ("width", 8, "dimensions"),
        ("protected_polygons", [[[0, 0], [8, 0], [0, 1]]], "in-bounds"),
        ("protected_polygons", [[[0, 0], [1, 1]]], "three"),
    ]:
        annotations.write_text(json.dumps({**original, field: value}))
        with pytest.raises(ValueError, match=message):
            cutout_png(source, output, annotations)
        assert not output.exists()
    annotations.write_text(json.dumps(original))
    with pytest.raises(ValueError, match="distinct"):
        cutout_png(source, source, annotations)
    with pytest.raises(ValueError, match="distinct"):
        cutout_png(source, annotations, annotations)


def test_cli_validation_error_is_clean_and_utf8_annotations_are_portable(png_source, tmp_path, capsys):
    source, annotations = png_source
    data = json.loads(annotations.read_text())
    annotations.write_text(json.dumps({**data, "note": "pale café paper"}, ensure_ascii=False), encoding="utf-8")
    arguments = ["cutout", str(source), str(tmp_path / "output.png"), "--annotations", str(annotations)]
    assert main([*arguments, "--dry-run"]) == 0
    json.loads(capsys.readouterr().out)
    annotations.write_text(json.dumps({**data, "source_sha256": "0" * 64}), encoding="utf-8")
    assert main(arguments) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("cutout: Annotation source hash")
    assert "Traceback" not in captured.err
