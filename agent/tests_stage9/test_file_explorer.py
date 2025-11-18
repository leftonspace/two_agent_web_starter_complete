"""
Tests for the file_explorer module.

STAGE 9: Tests file tree generation, content reading, snapshots, and diffs.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(agent_dir))

import file_explorer


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure for testing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create some files and directories
    (project_dir / "index.html").write_text("<html><body>Hello</body></html>")
    (project_dir / "style.css").write_text("body { color: red; }")

    subdir = project_dir / "js"
    subdir.mkdir()
    (subdir / "app.js").write_text("console.log('test');")

    # Create .history directory with snapshots
    history = project_dir / ".history"
    history.mkdir()

    snap1 = history / "iteration_1"
    snap1.mkdir()
    (snap1 / "index.html").write_text("<html><body>Hello v1</body></html>")

    snap2 = history / "iteration_2"
    snap2.mkdir()
    (snap2 / "index.html").write_text("<html><body>Hello v2</body></html>")

    return project_dir


def test_is_safe_path_valid(tmp_path):
    """Test that is_safe_path allows valid paths."""
    base = tmp_path / "project"
    base.mkdir()

    safe_path = base / "subdir" / "file.txt"
    assert file_explorer.is_safe_path(base, safe_path)


def test_is_safe_path_traversal(tmp_path):
    """Test that is_safe_path blocks directory traversal."""
    base = tmp_path / "project"
    base.mkdir()

    # Try to escape using ../
    unsafe_path = base / ".." / "other" / "file.txt"
    assert not file_explorer.is_safe_path(base, unsafe_path)


def test_is_text_file_by_extension(tmp_path):
    """Test text file detection by extension."""
    text_file = tmp_path / "test.txt"
    text_file.write_text("Hello")

    binary_file = tmp_path / "test.png"
    binary_file.write_bytes(b'\x89PNG\r\n\x1a\n')

    assert file_explorer.is_text_file(text_file)
    assert not file_explorer.is_text_file(binary_file)


def test_is_text_file_by_content(tmp_path):
    """Test text file detection by content (no extension)."""
    # Text file without extension
    text_file = tmp_path / "README"
    text_file.write_text("This is a README file")
    assert file_explorer.is_text_file(text_file)

    # Binary file without extension (contains null bytes)
    binary_file = tmp_path / "binary_data"
    binary_file.write_bytes(b'Hello\x00World\x00')
    assert not file_explorer.is_text_file(binary_file)


def test_get_project_tree(temp_project):
    """Test file tree generation."""
    tree = file_explorer.get_project_tree(temp_project)

    # Should have 3 items at root: index.html, style.css, js/
    assert len(tree) == 3

    # Check that directories and files are identified correctly
    names = {item["name"] for item in tree}
    assert "index.html" in names
    assert "style.css" in names
    assert "js" in names

    # Check directory vs file
    js_dir = next(item for item in tree if item["name"] == "js")
    assert js_dir["is_dir"]

    index_file = next(item for item in tree if item["name"] == "index.html")
    assert not index_file["is_dir"]
    assert index_file["size"] > 0


def test_get_project_tree_subdirectory(temp_project):
    """Test file tree generation for subdirectory."""
    tree = file_explorer.get_project_tree(temp_project, Path("js"))

    # Should have 1 item: app.js
    assert len(tree) == 1
    assert tree[0]["name"] == "app.js"
    assert not tree[0]["is_dir"]


def test_get_project_tree_skips_hidden(tmp_path):
    """Test that file tree skips hidden files (except .history)."""
    project = tmp_path / "project"
    project.mkdir()

    (project / "visible.txt").write_text("visible")
    (project / ".hidden").write_text("hidden")

    history = project / ".history"
    history.mkdir()

    tree = file_explorer.get_project_tree(project)

    names = {item["name"] for item in tree}
    assert "visible.txt" in names
    assert ".hidden" not in names
    assert ".history" in names  # .history should be included


def test_get_file_content_success(temp_project):
    """Test reading file content successfully."""
    result = file_explorer.get_file_content(temp_project, "index.html")

    assert result["content"] == "<html><body>Hello</body></html>"
    assert result["error"] is None
    assert not result["is_binary"]
    assert not result["is_too_large"]


def test_get_file_content_not_found(temp_project):
    """Test reading non-existent file."""
    result = file_explorer.get_file_content(temp_project, "nonexistent.txt")

    assert result["content"] is None
    assert "not found" in result["error"]


def test_get_file_content_path_traversal(temp_project):
    """Test that file reading blocks path traversal."""
    result = file_explorer.get_file_content(temp_project, "../../../etc/passwd")

    assert result["content"] is None
    assert "Access denied" in result["error"]


def test_get_file_content_binary_file(tmp_path):
    """Test reading binary file."""
    project = tmp_path / "project"
    project.mkdir()

    binary_file = project / "image.png"
    binary_file.write_bytes(b'\x89PNG\r\n\x1a\n')

    result = file_explorer.get_file_content(project, "image.png")

    assert result["content"] is None
    assert "Binary file" in result["error"]
    assert result["is_binary"]


def test_get_file_content_too_large(tmp_path):
    """Test reading file that exceeds size limit."""
    project = tmp_path / "project"
    project.mkdir()

    large_file = project / "large.txt"
    # Create file larger than MAX_FILE_SIZE (5MB)
    large_file.write_text("x" * (6 * 1024 * 1024))

    result = file_explorer.get_file_content(project, "large.txt")

    assert result["content"] is None
    assert "too large" in result["error"]
    assert result["is_too_large"]


def test_list_snapshots(temp_project):
    """Test listing project snapshots."""
    snapshots = file_explorer.list_snapshots(temp_project)

    assert len(snapshots) == 2
    assert snapshots[0].iteration == 1
    assert snapshots[1].iteration == 2
    assert snapshots[0].id == "iteration_1"
    assert snapshots[1].id == "iteration_2"


def test_list_snapshots_no_history(tmp_path):
    """Test listing snapshots when .history doesn't exist."""
    project = tmp_path / "project"
    project.mkdir()

    snapshots = file_explorer.list_snapshots(project)

    assert len(snapshots) == 0


def test_compute_diff_identical_files(tmp_path):
    """Test diff computation for identical files."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    content = "Line 1\nLine 2\nLine 3\n"
    file1.write_text(content)
    file2.write_text(content)

    result = file_explorer.compute_diff(file1, file2)

    assert "identical" in result["diff"].lower()
    assert result["error"] is None
    assert not result["is_binary"]


def test_compute_diff_different_files(tmp_path):
    """Test diff computation for different files."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    file1.write_text("Line 1\nLine 2\nLine 3\n")
    file2.write_text("Line 1\nModified Line 2\nLine 3\n")

    result = file_explorer.compute_diff(file1, file2)

    assert result["diff"] is not None
    assert result["error"] is None
    assert "-Line 2" in result["diff"]
    assert "+Modified Line 2" in result["diff"]


def test_compute_diff_file_added(tmp_path):
    """Test diff when file is added (doesn't exist in source)."""
    file1 = tmp_path / "nonexistent.txt"
    file2 = tmp_path / "new.txt"

    file2.write_text("New content\n")

    result = file_explorer.compute_diff(file1, file2)

    assert result["file1_missing"]
    assert not result["file2_missing"]
    assert "+New content" in result["diff"]


def test_compute_diff_file_deleted(tmp_path):
    """Test diff when file is deleted (doesn't exist in target)."""
    file1 = tmp_path / "old.txt"
    file2 = tmp_path / "nonexistent.txt"

    file1.write_text("Old content\n")

    result = file_explorer.compute_diff(file1, file2)

    assert not result["file1_missing"]
    assert result["file2_missing"]
    assert "-Old content" in result["diff"]


def test_compute_diff_both_missing(tmp_path):
    """Test diff when both files are missing."""
    file1 = tmp_path / "missing1.txt"
    file2 = tmp_path / "missing2.txt"

    result = file_explorer.compute_diff(file1, file2)

    assert result["file1_missing"]
    assert result["file2_missing"]
    assert "Both files are missing" in result["diff"]


def test_compute_diff_binary_files(tmp_path):
    """Test diff for binary files."""
    file1 = tmp_path / "file1.bin"
    file2 = tmp_path / "file2.bin"

    file1.write_bytes(b'\x89PNG\r\n\x1a\n')
    file2.write_bytes(b'\x89PNG\r\n\x1a\n')

    result = file_explorer.compute_diff(file1, file2)

    assert result["is_binary"]
    assert "Binary files" in result["diff"]


def test_snapshot_dataclass():
    """Test Snapshot dataclass."""
    snapshot = file_explorer.Snapshot(
        id="iteration_1",
        iteration=1,
        path="/path/to/snapshot",
        created_at="1234567890",
    )

    assert snapshot.id == "iteration_1"
    assert snapshot.iteration == 1
    assert snapshot.path == "/path/to/snapshot"
    assert snapshot.created_at == "1234567890"


def test_file_node_dataclass():
    """Test FileNode dataclass."""
    # File node
    file_node = file_explorer.FileNode(
        name="test.txt",
        path="dir/test.txt",
        is_dir=False,
        size=1024,
    )

    assert file_node.name == "test.txt"
    assert file_node.path == "dir/test.txt"
    assert not file_node.is_dir
    assert file_node.size == 1024

    # Directory node
    dir_node = file_explorer.FileNode(
        name="subdir",
        path="dir/subdir",
        is_dir=True,
    )

    assert dir_node.is_dir
    assert dir_node.size is None
    assert dir_node.children is None
