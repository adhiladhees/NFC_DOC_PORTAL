#!/usr/bin/env python3
"""
Export the current repository into Claude-friendly Markdown context bundles.

Usage:
  python scripts/export_for_claude.py
  python scripts/export_for_claude.py --max-chars 180000 --output-dir exports
"""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "exports",
}

DEFAULT_EXCLUDE_FILES = {
    "db.sqlite3",
}

TEXT_EXTENSIONS = {
    ".py",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".env",
    ".sql",
    ".xml",
    ".sh",
    ".ps1",
    ".bat",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the repo root (default: current directory).",
    )
    parser.add_argument(
        "--output-dir",
        default="exports",
        help="Directory for generated output files (default: exports).",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=180_000,
        help="Max characters per output file (default: 180000).",
    )
    return parser.parse_args()


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    try:
        with path.open("rb") as f:
            chunk = f.read(4096)
        if b"\x00" in chunk:
            return False
        chunk.decode("utf-8")
        return True
    except Exception:
        return False


def should_skip(path: Path, repo_root: Path) -> bool:
    rel = path.relative_to(repo_root)
    parts = set(rel.parts)
    if parts & DEFAULT_EXCLUDE_DIRS:
        return True
    if path.name in DEFAULT_EXCLUDE_FILES:
        return True
    if path.suffix.lower() in {".pyc", ".pyo", ".pyd", ".sqlite3", ".db"}:
        return True
    return False


def get_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path, repo_root):
            continue
        if not is_text_file(path):
            continue
        files.append(path)
    return sorted(files, key=lambda p: str(p.relative_to(repo_root)).lower())


def render_tree(files: list[Path], repo_root: Path) -> str:
    lines = ["Project files included:"]
    for path in files:
        rel = path.relative_to(repo_root).as_posix()
        lines.append(f"- {rel}")
    return "\n".join(lines) + "\n"


def line_numbered_text(content: str) -> str:
    numbered = []
    for idx, line in enumerate(content.splitlines(), start=1):
        numbered.append(f"{idx:04d} | {line}")
    if content.endswith("\n"):
        numbered.append(f"{len(numbered) + 1:04d} |")
    return "\n".join(numbered)


def render_file_block(path: Path, repo_root: Path) -> str:
    rel = path.relative_to(repo_root).as_posix()
    raw = path.read_text(encoding="utf-8", errors="replace")
    body = line_numbered_text(raw)
    return (
        f"\n## File: {rel}\n"
        f"```text\n{body}\n```\n"
    )


def build_parts(files: list[Path], repo_root: Path, max_chars: int) -> list[str]:
    header = (
        "# Repository Context Export\n\n"
        "Use this as source context. Paths and line numbers are preserved.\n\n"
    )
    tree = render_tree(files, repo_root) + "\n"
    static_prefix = header + tree

    parts: list[str] = []
    current = static_prefix

    for path in files:
        block = render_file_block(path, repo_root)
        if len(block) > max_chars:
            # Single large file: put it in its own part.
            if current != static_prefix:
                parts.append(current)
                current = static_prefix
            parts.append(static_prefix + block)
            continue
        if len(current) + len(block) > max_chars and current != static_prefix:
            parts.append(current)
            current = static_prefix
        current += block

    if current != static_prefix:
        parts.append(current)
    return parts


def write_prompt_file(output_dir: Path, part_count: int) -> None:
    prompt = (
        "Paste this instruction into Claude, then upload/paste all generated parts:\n\n"
        "You are reading a full repository export split into parts.\n"
        "Treat all parts as one project.\n"
        "First, confirm you loaded every part.\n"
        "Then give me:\n"
        "1) architecture overview,\n"
        "2) file-by-file explanation,\n"
        "3) risky bugs or logic issues,\n"
        "4) concrete refactor suggestions.\n"
        f"Expected part count: {part_count}\n"
    )
    (output_dir / "claude_prompt.txt").write_text(prompt, encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    output_dir = (repo_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    files = get_files(repo_root)
    if not files:
        raise SystemExit("No text files found to export.")

    parts = build_parts(files, repo_root, args.max_chars)
    for i, content in enumerate(parts, start=1):
        part_path = output_dir / f"claude_context_part{i:02d}.md"
        part_path.write_text(content, encoding="utf-8")

    write_prompt_file(output_dir, len(parts))

    print(f"Exported {len(files)} files into {len(parts)} part(s).")
    print(f"Output folder: {output_dir}")
    print("Files:")
    for i in range(1, len(parts) + 1):
        print(f"- claude_context_part{i:02d}.md")
    print("- claude_prompt.txt")


if __name__ == "__main__":
    main()
