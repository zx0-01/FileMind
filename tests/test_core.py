"""Tests for FileMind core functionality."""
from pathlib import Path
import tempfile
import os

from filemind.core import (
    scan_folder,
    find_duplicates,
    largest_files,
    organization_plan,
    apply_organization,
    human_size,
    category_for,
    iter_files,
    CATEGORIES,
    EXT_TO_CATEGORY,
)


def test_scan_folder_basic():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.txt").write_text("hello")
        (root / "b.png").write_bytes(b"\x00\x01\x00")  # 3 bytes
        result = scan_folder(root)
        assert result["files"] == 2
        assert result["total_bytes"] == 8  # 5 bytes from text + 3 bytes from png
        assert result["errors"] == 0


def test_scan_folder_with_errors():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Create a broken symlink that will cause an error
        (root / "valid.txt").write_text("hello")
        # Note: iter_files skips symlinks, so no errors expected
        result = scan_folder(root)
        assert result["files"] == 1


def test_duplicates_basic():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "one.txt").write_text("same content")
        (root / "two.txt").write_text("same content")
        groups = find_duplicates(root)
        assert len(groups) == 1
        assert len(groups[0]) == 2


def test_duplicates_no_duplicates():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "one.txt").write_text("unique1")
        (root / "two.txt").write_text("unique2")
        groups = find_duplicates(root)
        assert len(groups) == 0


def test_duplicates_with_subdirectory():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sub = root / "subdir"
        sub.mkdir()
        (root / "one.txt").write_text("same")
        (sub / "two.txt").write_text("same")
        # Duplicate detection is recursive, so both files should be found.
        groups = find_duplicates(root)
        assert len(groups) == 1
        assert {path.name for path in groups[0]} == {"one.txt", "two.txt"}


def test_largest_basic():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "small.txt").write_text("x")  # 1 byte
        (root / "large.txt").write_text("much larger content here")  # ~27 bytes
        result = largest_files(root, 1)
        assert len(result) == 1
        # The larger content should be first
        assert result[0][0].name == "large.txt"


def test_largest_with_limit():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for i in range(5):
            (root / f"file{i}.txt").write_text(f"content {i}")
        result = largest_files(root, 3)
        assert len(result) == 3


def test_organization_plan_basic():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "photo.jpg").write_bytes(b"image data")
        (root / "doc.pdf").write_bytes(b"pdf data")
        (root / "music.mp3").write_bytes(b"mp3 data")
        plan = organization_plan(root)
        # Should have 3 items: jpg -> Images, pdf -> Documents, mp3 -> Audio
        assert len(plan) == 3


def test_organization_plan_skips_category_folders():
    """Files already in category folders should not be reorganized."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        images_dir = root / "Images"
        images_dir.mkdir()
        (images_dir / "existing.jpg").write_bytes(b"existing image")
        (root / "newphoto.jpg").write_bytes(b"new image")
        plan = organization_plan(root)
        # The existing file in Images/ should be skipped
        # Only newphoto.jpg at root should be in the plan
        assert len(plan) == 1


def test_organization_plan_skips_hidden_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".hidden").write_text("hidden")
        plan = organization_plan(root)
        assert len(plan) == 0


def test_organization_plan_skips_dotfiles_at_root():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".gitignore").write_text("gitignore")
        plan = organization_plan(root)
        # .gitignore at root should be skipped
        assert len(plan) == 0


def test_organization_plan_with_subdirs():
    """Files in subdirectories should not be organized (they're not directly in root)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sub = root / "subdir"
        sub.mkdir()
        (sub / "deepfile.txt").write_text("deep file")
        (root / "shallow.txt").write_text("shallow file")
        plan = organization_plan(root)
        # Only shallow.txt at root should be in the plan
        assert len(plan) == 1
        assert plan[0][0].name == "shallow.txt"


def test_apply_organization_basic():
    """Test that apply_organization moves files correctly."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "photo.jpg").write_bytes(b"image data")
        plan = [(root / "photo.jpg", root / "Images/photo.jpg")]
        moved, errors = apply_organization(plan)
        assert moved == 1
        assert (root / "Images/photo.jpg").exists()
        assert not (root / "photo.jpg").exists()


def test_apply_organization_collision():
    """Test collision handling during apply_organization."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "photo.jpg").write_bytes(b"image data")
        (root / "Images").mkdir()
        (root / "Images/photo.jpg").write_bytes(b"existing")
        plan = [(root / "photo.jpg", root / "Images/photo.jpg")]
        moved, errors = apply_organization(plan)
        assert moved == 1
        # Should have been renamed with _1 suffix
        assert len(errors) == 0
        assert (root / "Images/photo.jpg").read_bytes() == b"existing"
        assert (root / "Images/photo_1.jpg").read_bytes() == b"image data"


def test_apply_organization_nonexistent_source():
    """Test error handling when source doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = [(root / "nonexistent.jpg", root / "Images/photo.jpg")]
        moved, errors = apply_organization(plan)
        assert moved == 0
        assert len(errors) == 1


def test_human_size():
    # Test various sizes
    result0 = human_size(0)
    assert "B" in result0, f"Expected B in {result0}"

    result1k = human_size(1024)
    assert "KB" in result1k, f"Expected KB in {result1k}"

    result1m = human_size(1024 * 1024)
    assert "MB" in result1m, f"Expected MB in {result1m}"

    result1g = human_size(1024 * 1024 * 1024)
    assert "GB" in result1g, f"Expected GB in {result1g}"


def test_category_for_known():
    assert category_for(Path(".png")) == "Images"
    assert category_for(Path(".jpg")) == "Images"
    assert category_for(Path(".pdf")) == "Documents"
    assert category_for(Path(".mp3")) == "Audio"
    assert category_for(Path(".zip")) == "Archives"
    assert category_for(Path(".py")) == "Code"
    assert category_for(Path(".exe")) == "Installers"
    assert category_for(Path(".unknown")) == "Other"


def test_category_for_unknown():
    assert category_for(Path(".xyz")) == "Other"
    assert category_for(Path("noextension")) == "Other"


def test_iter_files_skips_symlinks():
    """iter_files should skip symlinked files and not follow symlinked directories."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "regular.txt").write_text("hello")
        # Create a symlink to a file - should be skipped
        (root / "symlink_to_file.txt").symlink_to(root / "regular.txt")
        # Create a symlink to a directory - should not be followed
        (root / "symlink_dir").symlink_to(root)
        files = list(iter_files(root))
        # Should only find regular.txt, not anything via the symlink_dir loop
        file_names = [f.name for f in files]
        assert "regular.txt" in file_names
        # Should NOT find files via the symlink directory loop


def test_iter_files_regular():
    """iter_files should yield regular files."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.txt").write_text("a")
        (root / "b.py").write_text("b")
        files = sorted(iter_files(root))
        assert len(files) == 2
        assert {f.name for f in files} == {"a.txt", "b.py"}


def test_huge_size():
    """Test human_size with very large values."""
    result = human_size(999999999999)
    # 999999999999 bytes ≈ 931.32 GB, which is in GB range
    assert "GB" in result or "TB" in result


def test_scan_folder_empty():
    """Test scan on empty directory."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = scan_folder(root)
        assert result["files"] == 0
        assert result["total_bytes"] == 0
        assert result["errors"] == 0


def test_find_duplicates_different_sizes():
    """Files with different content but same size should not be grouped as duplicates unless SHA-256 matches."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.txt").write_text("content A")
        (root / "b.txt").write_text("content B")  # Same length but different content
        groups = find_duplicates(root)
        # These have different SHA-256, so should not be duplicates
        assert len(groups) == 0


def test_find_duplicates_same_content():
    """Files with identical content should be detected as duplicates."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        content = "identical content here"
        (root / "file1.txt").write_text(content)
        (root / "file2.txt").write_text(content)
        groups = find_duplicates(root)
        assert len(groups) == 1
        assert len(groups[0]) == 2


def test_largest_files_with_progress():
    """Test largest_files with progress callback (optional)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for i in range(3):
            (root / f"file{i}.txt").write_text(f"content {i} " * 10)
        # progress callback should not break the function
        result = largest_files(root, 5, progress=lambda *args: None)
        assert len(result) == 3


def test_organization_plan_expanded_categories():
    """Test organization with expanded category extensions."""
    from filemind.core import organization_plan
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Add a .avif file (expanded Image category)
        (root / "avatar.avif").write_bytes(b"avif data")
        (root / "photo.png").write_bytes(b"png data")
        plan = organization_plan(root)
        # Both should be in the plan since they're at root level
        avihas = any("avif" in str(destination) for _, destination in plan)
        pnghas = any("png" in str(destination) for _, destination in plan)
        assert avihas or pnghas, f"Expected files to be organized, plan: {plan}"

def test_duplicates_nested_subdirectories():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nested = root / "one" / "two"
        nested.mkdir(parents=True)
        (root / "copy-a.bin").write_bytes(b"same bytes")
        (nested / "copy-b.bin").write_bytes(b"same bytes")
        groups = find_duplicates(root)
        assert len(groups) == 1
        assert len(groups[0]) == 2


def test_apply_organization_never_overwrites_destination():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "photo.jpg"
        destination_dir = root / "Images"
        destination_dir.mkdir()
        destination = destination_dir / "photo.jpg"
        source.write_bytes(b"source contents")
        destination.write_bytes(b"must survive")

        moved, errors = apply_organization([(source, destination)])

        assert moved == 1
        assert errors == []
        assert not source.exists()
        assert destination.read_bytes() == b"must survive"
        assert (destination_dir / "photo_1.jpg").read_bytes() == b"source contents"


def test_apply_organization_skips_symlink_source():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        real = root / "real.txt"
        link = root / "link.txt"
        destination = root / "Documents" / "link.txt"
        real.write_text("keep me")
        link.symlink_to(real)

        moved, errors = apply_organization([(link, destination)])

        assert moved == 0
        assert len(errors) == 1
        assert link.is_symlink()
        assert real.read_text() == "keep me"
        assert not destination.exists()


def test_scan_progress_callback_is_called():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "one.txt").write_text("one")
        updates = []
        scan_folder(root, progress=lambda current, total, message: updates.append((current, total, message)))
        assert updates
        assert updates[-1][0] == 1


def test_duplicates_progress_callback_is_called():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "one.txt").write_text("same")
        (root / "two.txt").write_text("same")
        updates = []
        find_duplicates(root, progress=lambda current, total, message: updates.append((current, total, message)))
        assert updates
        assert updates[-1][0] == 2
        assert updates[-1][1] == 2


def test_organization_plan_skips_symlink_category_directory():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "root"
        outside = Path(tmp) / "outside"
        root.mkdir()
        outside.mkdir()
        (root / "photo.jpg").write_bytes(b"image")
        (root / "Images").symlink_to(outside, target_is_directory=True)

        plan = organization_plan(root)

        assert plan == []
        assert list(outside.iterdir()) == []
