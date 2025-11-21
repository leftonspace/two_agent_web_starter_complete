"""
Tests for file system operations.

PHASE 8.3: Tests for safe file operations with workspace restrictions.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from agent.actions.file_ops import FileOperations
from agent.actions.git_ops import GitOps


# ══════════════════════════════════════════════════════════════════════
# File Operations Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def temp_workspace():
    """Create temporary workspace"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_read_write_file(temp_workspace):
    """Test basic read and write operations"""
    ops = FileOperations(temp_workspace)

    content = "Hello, World!"
    await ops.write_file("test.txt", content)

    read_content = await ops.read_file("test.txt")
    assert read_content == content


@pytest.mark.asyncio
async def test_path_validation_prevents_escape(temp_workspace):
    """Test path validation prevents directory traversal"""
    ops = FileOperations(temp_workspace)

    # Try to escape workspace
    with pytest.raises(ValueError, match="outside workspace"):
        await ops.read_file("../../../etc/passwd")


@pytest.mark.asyncio
async def test_system_path_blocked(temp_workspace):
    """Test system paths are blocked"""
    ops = FileOperations(temp_workspace)

    # Try to access system directory
    with pytest.raises(ValueError, match="system files denied"):
        await ops.read_file("/etc/passwd")


@pytest.mark.asyncio
async def test_create_delete_directory(temp_workspace):
    """Test directory creation and deletion"""
    ops = FileOperations(temp_workspace)

    await ops.create_directory("test_dir")
    assert ops.directory_exists("test_dir")

    await ops.delete_directory("test_dir")
    assert not ops.directory_exists("test_dir")


@pytest.mark.asyncio
async def test_list_files(temp_workspace):
    """Test listing files"""
    ops = FileOperations(temp_workspace)

    # Create some files
    await ops.write_file("file1.txt", "content1")
    await ops.write_file("file2.txt", "content2")
    await ops.write_file("file3.md", "content3")

    # List all files
    files = await ops.list_files()
    assert len(files) == 3
    assert "file1.txt" in files
    assert "file2.txt" in files
    assert "file3.md" in files


@pytest.mark.asyncio
async def test_list_files_with_pattern(temp_workspace):
    """Test listing files with glob pattern"""
    ops = FileOperations(temp_workspace)

    # Create files
    await ops.write_file("test1.py", "content")
    await ops.write_file("test2.py", "content")
    await ops.write_file("test.txt", "content")

    # List only .py files
    py_files = await ops.list_files(pattern="*.py")
    assert len(py_files) == 2
    assert all(f.endswith('.py') for f in py_files)


@pytest.mark.asyncio
async def test_file_exists(temp_workspace):
    """Test file existence check"""
    ops = FileOperations(temp_workspace)

    assert not ops.file_exists("nonexistent.txt")

    await ops.write_file("exists.txt", "content")
    assert ops.file_exists("exists.txt")


@pytest.mark.asyncio
async def test_get_file_info(temp_workspace):
    """Test getting file metadata"""
    ops = FileOperations(temp_workspace)

    content = "Test content"
    await ops.write_file("info_test.txt", content)

    info = await ops.get_file_info("info_test.txt")

    assert info["path"] == "info_test.txt"
    assert info["size"] == len(content.encode('utf-8'))
    assert info["is_file"] is True
    assert info["is_dir"] is False
    assert "created" in info
    assert "modified" in info


@pytest.mark.asyncio
async def test_append_file(temp_workspace):
    """Test appending to file"""
    ops = FileOperations(temp_workspace)

    await ops.write_file("append_test.txt", "Line 1\n")
    await ops.append_file("append_test.txt", "Line 2\n")

    content = await ops.read_file("append_test.txt")
    assert content == "Line 1\nLine 2\n"


@pytest.mark.asyncio
async def test_copy_file(temp_workspace):
    """Test copying file"""
    ops = FileOperations(temp_workspace)

    content = "Original content"
    await ops.write_file("original.txt", content)

    await ops.copy_file("original.txt", "copy.txt")

    # Both should exist
    assert ops.file_exists("original.txt")
    assert ops.file_exists("copy.txt")

    # Content should be same
    copy_content = await ops.read_file("copy.txt")
    assert copy_content == content


@pytest.mark.asyncio
async def test_move_file(temp_workspace):
    """Test moving/renaming file"""
    ops = FileOperations(temp_workspace)

    content = "Move me"
    await ops.write_file("before.txt", content)

    await ops.move_file("before.txt", "after.txt")

    # Original should not exist
    assert not ops.file_exists("before.txt")

    # New location should exist with same content
    assert ops.file_exists("after.txt")
    moved_content = await ops.read_file("after.txt")
    assert moved_content == content


@pytest.mark.asyncio
async def test_delete_file(temp_workspace):
    """Test file deletion"""
    ops = FileOperations(temp_workspace)

    await ops.write_file("delete_me.txt", "content")
    assert ops.file_exists("delete_me.txt")

    await ops.delete_file("delete_me.txt")
    assert not ops.file_exists("delete_me.txt")


@pytest.mark.asyncio
async def test_max_file_size_limit(temp_workspace):
    """Test file size limit enforcement"""
    ops = FileOperations(temp_workspace, max_file_size=100)

    # Small file should work
    await ops.write_file("small.txt", "x" * 50)

    # Large file should fail
    with pytest.raises(ValueError, match="too large"):
        await ops.write_file("large.txt", "x" * 200)


@pytest.mark.asyncio
async def test_nested_directories(temp_workspace):
    """Test operations in nested directories"""
    ops = FileOperations(temp_workspace)

    # Create nested structure
    await ops.create_directory("level1/level2/level3")
    await ops.write_file("level1/level2/level3/deep.txt", "deep content")

    # Read from nested path
    content = await ops.read_file("level1/level2/level3/deep.txt")
    assert content == "deep content"


@pytest.mark.asyncio
async def test_list_directories(temp_workspace):
    """Test listing directories"""
    ops = FileOperations(temp_workspace)

    # Create directories
    await ops.create_directory("dir1")
    await ops.create_directory("dir2")
    await ops.create_directory("dir3")

    directories = await ops.list_directories()
    assert len(directories) == 3
    assert "dir1" in directories
    assert "dir2" in directories
    assert "dir3" in directories


# ══════════════════════════════════════════════════════════════════════
# Git Operations Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
async def git_repo(temp_workspace):
    """Create git repository"""
    git = GitOps(temp_workspace)
    await git.init()
    return git


@pytest.mark.asyncio
async def test_git_init(temp_workspace):
    """Test git repository initialization"""
    git = GitOps(temp_workspace)
    await git.init()

    is_repo = await git.is_repo()
    assert is_repo is True


@pytest.mark.asyncio
async def test_git_add_commit(git_repo, temp_workspace):
    """Test adding and committing files"""
    # Create a file
    test_file = Path(temp_workspace) / "test.txt"
    test_file.write_text("Test content")

    # Add and commit
    await git_repo.add("test.txt")
    await git_repo.commit("Initial commit")

    # Check log
    log = await git_repo.get_log(max_count=1)
    assert len(log) > 0
    assert "Initial commit" in log[0]


@pytest.mark.asyncio
async def test_git_status(git_repo, temp_workspace):
    """Test getting repository status"""
    # Create untracked file
    test_file = Path(temp_workspace) / "untracked.txt"
    test_file.write_text("Untracked")

    status = await git_repo.get_status()

    assert "untracked.txt" in status["untracked"]
    assert status["clean"] is False


@pytest.mark.asyncio
async def test_git_branch_operations(git_repo, temp_workspace):
    """Test branch creation and management"""
    # Create initial commit
    test_file = Path(temp_workspace) / "test.txt"
    test_file.write_text("Test")
    await git_repo.add(".")
    await git_repo.commit("Initial commit")

    # Create branch
    await git_repo.create_branch("feature", checkout=False)

    branches = await git_repo.get_branches()
    assert "feature" in branches

    # Checkout branch
    await git_repo.checkout("feature")
    current = await git_repo.get_current_branch()
    assert current == "feature"


@pytest.mark.asyncio
async def test_git_get_log(git_repo, temp_workspace):
    """Test getting commit log"""
    # Create multiple commits
    for i in range(3):
        test_file = Path(temp_workspace) / f"file{i}.txt"
        test_file.write_text(f"Content {i}")
        await git_repo.add(".")
        await git_repo.commit(f"Commit {i}")

    log = await git_repo.get_log(max_count=3)
    assert len(log) == 3


@pytest.mark.asyncio
async def test_git_remotes(git_repo):
    """Test remote management"""
    # Add remote
    await git_repo.add_remote("origin", "https://github.com/user/repo.git")

    remotes = await git_repo.get_remotes()
    assert "origin" in remotes
    assert remotes["origin"] == "https://github.com/user/repo.git"

    # Remove remote
    await git_repo.remove_remote("origin")
    remotes = await git_repo.get_remotes()
    assert "origin" not in remotes
