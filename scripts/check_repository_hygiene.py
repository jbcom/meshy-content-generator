"""Run lightweight, deterministic checks used by pre-commit and CI."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

import yaml

MAX_FILE_BYTES = 500_000
PRIVATE_KEY = re.compile(rb"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----")
CONFLICT = re.compile(r"^(?:<{7}|={7}|>{7})(?: .*)?$", re.MULTILINE)


def _check(path: Path) -> list[str]:
    """Return all hygiene violations for one existing text or config file."""
    if not path.is_file() or str(path).startswith((".git/", "docs/dist/", "node_modules/")):
        return []
    errors: list[str] = []
    payload = path.read_bytes()
    if len(payload) > MAX_FILE_BYTES:
        errors.append(f"{path}: exceeds {MAX_FILE_BYTES} byte pre-commit limit")
    if PRIVATE_KEY.search(payload):
        errors.append(f"{path}: contains a private-key marker")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return errors
    if text and not text.endswith("\n"):
        errors.append(f"{path}: missing final newline")
    if any(line.rstrip(" \t") != line for line in text.splitlines()):
        errors.append(f"{path}: trailing whitespace")
    if CONFLICT.search(text):
        errors.append(f"{path}: merge-conflict marker")
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            json.loads(text)
        elif suffix == ".toml":
            tomllib.loads(text)
        elif suffix in {".yaml", ".yml"}:
            yaml.safe_load(text)
    except (json.JSONDecodeError, tomllib.TOMLDecodeError, yaml.YAMLError) as error:
        errors.append(f"{path}: invalid {suffix[1:]}: {error}")
    return errors


def main(arguments: list[str] | None = None) -> int:
    """Check paths supplied by pre-commit, reporting every actionable error."""
    paths = [Path(argument) for argument in arguments or sys.argv[1:]]
    errors = [error for path in paths for error in _check(path)]
    if errors:
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
