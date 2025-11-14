from pathlib import Path

from site_tools import (
    write_iteration_snapshot,
    load_existing_files,
    summarize_files_for_manager,
)


def test_write_iteration_snapshot_and_load(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj"
    project_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "index.html": "<!doctype html><html><body>Hello</body></html>",
        "style.css": "body { background: #fff; }",
    }

    # simulate iteration 1, mode '3loop'
    snapshot_dir = write_iteration_snapshot(
        project_root=project_dir,
        iteration=1,
        mode="3loop",
        files=files,
    )

    # main files should also exist directly in project_dir
    for rel, content in files.items():
        target = project_dir / rel
        assert target.exists()
        assert target.read_text(encoding="utf-8") == content

    # snapshot directory should be created and contain the files
    assert snapshot_dir.exists()
    for rel, content in files.items():
        snap = snapshot_dir / rel
        assert snap.exists()
        assert snap.read_text(encoding="utf-8") == content

    # load_existing_files should see the main files
    loaded = load_existing_files(project_dir)
    assert set(loaded.keys()) == set(files.keys())
    assert loaded["index.html"].startswith("<!doctype html>")
    assert "background" in loaded["style.css"]

    # summarize_files_for_manager should return short previews
    summary = summarize_files_for_manager(loaded)
    assert isinstance(summary, list)
    assert any(entry["path"] == "index.html" for entry in summary)
    assert all("preview" in entry for entry in summary)
