from pathlib import Path
from filemind.core import find_duplicates, largest_files, organization_plan, scan_folder


def test_scan_folder(tmp_path: Path):
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "b.png").write_bytes(b"\x00\x01")
    result = scan_folder(tmp_path)
    assert result["files"] == 2
    assert result["total_bytes"] == 7


def test_duplicates(tmp_path: Path):
    (tmp_path / "one.txt").write_text("same")
    (tmp_path / "two.txt").write_text("same")
    groups = find_duplicates(tmp_path)
    assert len(groups) == 1
    assert len(groups[0]) == 2


def test_largest(tmp_path: Path):
    (tmp_path / "small.txt").write_text("x")
    (tmp_path / "large.txt").write_text("much larger")
    result = largest_files(tmp_path, 1)
    assert result[0][0].name == "large.txt"


def test_organization_plan_is_preview_only(tmp_path: Path):
    file_path = tmp_path / "photo.jpg"
    file_path.write_bytes(b"image")
    plan = organization_plan(tmp_path)
    assert len(plan) == 1
    assert file_path.exists()
    assert plan[0][1].parent.name == "Images"
