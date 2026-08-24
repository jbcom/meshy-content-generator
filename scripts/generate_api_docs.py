"""Generate the checked-in Sourcey API reference from the public Python API."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "meshy_content_generator"
OUTPUT = ROOT / "docs" / "api-reference.md"


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Return a stable, annotation-preserving signature for a callable."""
    return ast.unparse(node.args)


def _document_module(path: Path) -> list[str]:
    """Render public classes and functions from one module."""
    module = ast.parse(path.read_text(encoding="utf-8"))
    lines = [f"## `{path.stem}`", ""]
    for node in module.body:
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) or node.name.startswith("_"):
            continue
        docstring = ast.get_docstring(node) or "No public documentation is available."
        if isinstance(node, ast.ClassDef):
            lines.extend([f"### `{node.name}`", "", docstring, ""])
            for member in node.body:
                if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and not member.name.startswith("_"):
                    member_docstring = ast.get_docstring(member) or "No public documentation is available."
                    lines.extend([f"#### `{member.name}({_signature(member)})`", "", member_docstring, ""])
        else:
            lines.extend([f"### `{node.name}({_signature(node)})`", "", docstring, ""])
    return lines


def render() -> str:
    """Build the complete Markdown document without timestamps or environment data."""
    lines = [
        "---",
        "title: Python API reference",
        "description: Generated public API reference for meshy-content-generator.",
        "---",
        "",
        "# Python API reference",
        "",
        "This file is generated from public classes, functions, signatures, and docstrings in `src/`.",
        "Regenerate it with `pnpm --dir docs run generate-api`; CI rejects a stale result.",
        "",
    ]
    for source_path in sorted(SOURCE.glob("*.py")):
        if source_path.name != "__init__.py":
            lines.extend(_document_module(source_path))
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    """Write the generated reference only when content differs."""
    rendered = render()
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
        OUTPUT.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
