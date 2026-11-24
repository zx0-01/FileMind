from __future__ import annotations

import hashlib
import json
import os
import stat
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable

CATEGORIES = {
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".tiff", ".ico", ".heic", ".avif"},
    "Videos": {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".wmv", ".mpg", ".mpeg"},
    "Audio": {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus", ".wma"},
    "Documents": {".pdf", ".doc", ".docx", ".odt", ".txt", ".rtf", ".md", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".epub", ".mobi"},
    "Archives": {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar", ".ace"},
    "Code": {".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".cpp", ".c", ".h", ".java", ".rs", ".go", ".json", ".yaml", ".yml", ".toml", ".sh", ".sql", ".env"},
    "Installers": {".exe", ".msi", ".deb", ".rpm", ".appimage", ".dmg", ".pkg", ".jar"},
}
EXT_TO_CATEGORY = {ext: category for category, extensions in CATEGORIES.items() for ext in extensions}
ProgressCallback = Callable[[int, int, str], None]


def human_size(size: int) -> str:
    """Convert bytes to a human-readable size string."""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if value < 1024 or unit == "PB":
            return f"{value:.1f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
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
                if path.is_symlink():
                    continue
                if path.is_file():
                    yield path
            except OSError:
                continue


def category_for(path: Path) -> str:
    """Return a category for a file path, including dot-extension names."""
    ext = path.suffix.lower() or path.name.lower()
    return EXT_TO_CATEGORY.get(ext, "Other")


def scan_folder(root: Path, progress: ProgressCallback | None = None) -> dict[str, Any]:
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
        if progress:
            progress(count, 0, "Scanning files")
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


def find_duplicates(root: Path, progress: ProgressCallback | None = None) -> list[list[Path]]:
    """Find byte-identical regular files recursively using size + SHA-256."""
    root = validate_directory(root)
    files = list(iter_files(root))
    by_size: dict[int, list[Path]] = defaultdict(list)
    total_files = len(files)
    for idx, path in enumerate(files, 1):
        if progress:
            progress(idx, total_files, f"Checking {path.name}")
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


def largest_files(root: Path, limit: int = 10, progress: ProgressCallback | None = None) -> list[tuple[Path, int]]:
    root = validate_directory(root)
    items: list[tuple[Path, int]] = []
    files = list(iter_files(root))
    total_files = len(files)
    for idx, path in enumerate(files, 1):
        if progress:
            progress(idx, total_files, f"Checking {path.name}")
        try:
            items.append((path, path.stat().st_size))
        except OSError:
            continue
    return sorted(items, key=lambda item: item[1], reverse=True)[:max(1, limit)]


def largest_files_with_progress(root: Path, limit: int = 10, progress: ProgressCallback | None = None) -> list[tuple[Path, int]]:
    return largest_files(root, limit=limit, progress=progress)


def scan_folder_with_progress(root: Path, progress: ProgressCallback | None = None) -> dict[str, Any]:
    return scan_folder(root, progress=progress)


def find_duplicates_with_progress(root: Path, progress: ProgressCallback | None = None) -> list[list[Path]]:
    return find_duplicates(root, progress=progress)


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
    """Plan moves for visible files directly inside root; never flatten subfolders."""
    root = validate_directory(root)
    plan = []
    for source in iter_files(root):
        if source.parent != root or source.name.startswith("."):
            continue
        category = category_for(source)
        destination_dir = root / category
        # Never write through a pre-existing category-folder symlink.
        if destination_dir.is_symlink():
            continue
        if destination_dir.exists() and not destination_dir.is_dir():
            continue
        if source.parent == destination_dir or destination_dir in source.parents:
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


def _move_without_overwrite(source: Path, destination: Path) -> Path:
    """Move a file using an atomic no-clobber hard-link operation.

    The destination is created with os.link(), which fails if any file or
    symlink already exists there. The source is removed only after the link
    succeeds. This intentionally prefers a safe error over an unsafe fallback
    on filesystems that do not support hard links.
    """
    source_stat = source.lstat()
    if not stat.S_ISREG(source_stat.st_mode):
        raise OSError(f"Source is not a regular file: {source}")

    candidate = destination
    index = 0
    while True:
        try:
            os.link(source, candidate, follow_symlinks=False)
            break
        except FileExistsError:
            index += 1
            candidate = destination.with_name(
                f"{destination.stem}_{index}{destination.suffix}"
            )

    try:
        source.unlink()
    except OSError:
        # Roll back only the link we just created, and only if it still points
        # to the same inode. Never remove a path that another process replaced.
        try:
            if os.path.samefile(source, candidate):
                candidate.unlink()
        except OSError:
            pass
        raise
    return candidate


def apply_organization(plan: list[tuple[Path, Path]]) -> tuple[int, list[str]]:
    """Apply a plan without ever overwriting an existing destination file."""
    moved = 0
    errors = []
    for source, destination in plan:
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            _move_without_overwrite(source, destination)
            moved += 1
        except OSError as exc:
            errors.append(f"{source}: {exc}")
    return moved, errors


def write_report(data: dict[str, Any], output: Path) -> None:
    output = output.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")
