import os

import pytest

from v2.server.tools.loaders import load_markdown_files, resolve_relative_links


@pytest.fixture
def docs_dir(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()

    (docs / "install.md").write_text("# Install\nSome install instructions.")
    (docs / "config.md").write_text("# Config\nSee [install](./install.md) for setup.")

    sub = docs / "advanced"
    sub.mkdir()
    (sub / "tuning.md").write_text("# Tuning\nAdvanced tuning guide.")

    (docs / "README.md").write_text("# README\nThis should be excluded.")

    return docs


def test_load_markdown_files(docs_dir):
    files = load_markdown_files(str(docs_dir), "https://github.com/org/repo/tree/main")

    paths = {f.path for f in files}
    assert "install.md" in paths
    assert "config.md" in paths
    assert "advanced/tuning.md" in paths
    assert "README.md" not in paths


def test_content_hash_is_consistent(docs_dir):
    files1 = load_markdown_files(str(docs_dir), "https://github.com/org/repo/tree/main")
    files2 = load_markdown_files(str(docs_dir), "https://github.com/org/repo/tree/main")

    hashes1 = {f.path: f.content_hash for f in files1}
    hashes2 = {f.path: f.content_hash for f in files2}
    assert hashes1 == hashes2


def test_content_hash_changes_on_edit(docs_dir):
    files_before = load_markdown_files(str(docs_dir), "https://github.com/org/repo/tree/main")
    hash_before = {f.path: f.content_hash for f in files_before}

    (docs_dir / "install.md").write_text("# Install\nUpdated instructions.")

    files_after = load_markdown_files(str(docs_dir), "https://github.com/org/repo/tree/main")
    hash_after = {f.path: f.content_hash for f in files_after}

    assert hash_before["install.md"] != hash_after["install.md"]
    assert hash_before["config.md"] == hash_after["config.md"]


def test_url_generation(docs_dir):
    files = load_markdown_files(str(docs_dir), "https://github.com/org/repo/tree/main")
    file_map = {f.path: f for f in files}

    assert file_map["install.md"].url == "https://github.com/org/repo/tree/main/install.md"
    assert file_map["advanced/tuning.md"].url == "https://github.com/org/repo/tree/main/advanced/tuning.md"


def test_resolve_relative_links():
    content = "See [install](./install.md) and [external](https://example.com)."
    result = resolve_relative_links("docs/config.md", "https://github.com/org/repo/tree/main", content)

    assert "https://github.com/org/repo/tree/main/docs/./install.md" in result
    assert "https://example.com" in result
