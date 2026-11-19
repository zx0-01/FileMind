from __future__ import annotations

import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

CATEGORIES = {
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".tiff", ".ico", ".heic"},
    "Videos": {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".wmv"},
    "Audio": {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"},
    "Documents": {".pdf", ".doc", ".docx", ".odt", ".txt", ".rtf", ".md", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"},
    "Archives": {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar"},
    "Code": {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".cpp", ".c", ".h", ".java", ".rs", ".go", ".json", ".yaml", ".yml", ".toml", ".sh", ".sql"},
    "Installers": {".exe", ".msi", ".deb", ".rpm", ".appimage", ".dmg", ".pkg"},
}
EXT_TO_CATEGORY = {ext: category for category, extensions in CATEGORIES.items() for ext in extensions}


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def validate_directory(path: Path) -> Path:
    path = path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Folder does not exist: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"Not a folder: {path}")
    return path


def iter_files(root: Path) -> Iterable[Path]:
    """Walk regular files without following symlinks."""
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if not (Path(current) / d).is_symlink()]
        for name in names:
            path = Path(current) / name
            try:
                if path.is_file() and not path.is_symlink():
                    yield path
            except OSError:
                continue


def category_for(path: Path) -> str:
    return EXT_TO_CATEGORY.get(path.suffix.lower(), "Other")


def scan_folder(root: Path) -> dict[str, Any]:
    root = validate_directory(root)
    total_size = 0
    count = 0
    categories: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "bytes": 0})
    errors = 0
    for path in iter_files(root):
        try:
            size = path.stat().st_size
            category = category_for(path)
            count += 1
            total_size += size
            categories[category]["count"] += 1
            categories[category]["bytes"] += size
        except OSError:
            errors += 1
    return {
        "root": str(root),
        "files": count,
        "total_bytes": total_size,
        "categories": dict(sorted(categories.items())),
        "errors": errors,
    }


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_duplicates(root: Path) -> list[list[Path]]:
    root = validate_directory(root)
    by_size: dict[int, list[Path]] = defaultdict(list)
    for path in iter_files(root):
        try:
            by_size[path.stat().st_size].append(path)
        except OSError:
            continue
    groups: dict[str, list[Path]] = defaultdict(list)
    for size_group in by_size.values():
        if len(size_group) < 2:
            continue
        for path in size_group:
            try:
                groups[sha256_file(path)].append(path)
            except OSError:
                continue
    return [sorted(group) for group in groups.values() if len(group) > 1]


def largest_files(root: Path, limit: int = 10) -> list[tuple[Path, int]]:
    root = validate_directory(root)
    items: list[tuple[Path, int]] = []
    for path in iter_files(root):
        try:
            items.append((path, path.stat().st_size))
        except OSError:
            continue
    return sorted(items, key=lambda item: item[1], reverse=True)[:max(1, limit)]


def search_files(root: Path, query: str, extension: str | None = None) -> list[Path]:
    root = validate_directory(root)
    needle = query.casefold()
    ext = extension.casefold() if extension else None
    found = []
    for path in iter_files(root):
        if needle in path.name.casefold() and (ext is None or path.suffix.casefold() == ext):
            found.append(path)
    return sorted(found)


def organization_plan(root: Path) -> list[tuple[Path, Path]]:
    root = validate_directory(root)
    plan = []
    for source in iter_files(root):
        # Do not reorganize files already inside a category folder.
        if source.parent == root and source.name.startswith("."):
            continue
        category = category_for(source)
        destination_dir = root / category
        try:
            if source.parent == destination_dir or destination_dir in source.parents:
                continue
            # Only organize files directly in root to avoid unexpectedly flattening subfolders.
            if source.parent != root:
                continue
        except OSError:
            continue
        destination = destination_dir / source.name
        if destination.exists():
            stem, suffix = source.stem, source.suffix
            index = 1
            while (destination_dir / f"{stem}_{index}{suffix}").exists():
                index += 1
            destination = destination_dir / f"{stem}_{index}{suffix}"
        plan.append((source, destination))
    return plan


def apply_organization(plan: list[tuple[Path, Path]]) -> tuple[int, list[str]]:
    moved = 0
    errors = []
    for source, destination in plan:
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Re-check collision immediately before moving.
            if destination.exists():
                stem, suffix = destination.stem, destination.suffix
                index = 1
                while (destination.parent / f"{stem}_{index}{suffix}").exists():
                    index += 1
                destination = destination.parent / f"{stem}_{index}{suffix}"
            source.rename(destination)
            moved += 1
        except OSError as exc:
            errors.append(f"{source}: {exc}")
    return moved, errors


def write_report(data: dict[str, Any], output: Path) -> None:
    output = output.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")
