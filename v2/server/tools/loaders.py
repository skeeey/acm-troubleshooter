import hashlib
import logging
import os
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

link_pattern = re.compile(r"\[([^\]]+)\]\(([^ )]+)(?: \"([^\"]+)\")?\)")
relative_path_pattern = re.compile(r"^(?:\.{1,2}/)+")

DEFAULT_EXCLUDES = ["README.md", "SECURITY.md", "GUIDELINE.md", "index.md"]


@dataclass
class DocFile:
    path: str
    url: str
    content: str
    content_hash: str


def load_markdown_files(
    repo_dir: str,
    base_url: str,
    excludes: list[str] | None = None,
) -> list[DocFile]:
    if excludes is None:
        excludes = DEFAULT_EXCLUDES

    doc_files = []
    for root, dirs, files in os.walk(repo_dir):
        dirs[:] = [d for d in dirs if d != ".git"]

        if os.path.basename(root) in excludes:
            continue

        for f in files:
            if not f.endswith(".md") or f in excludes:
                continue

            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, repo_dir)

            with open(full_path, encoding="utf-8") as fh:
                content = fh.read()

            content = resolve_relative_links(rel_path, base_url, content)
            content_hash = hashlib.md5(content.encode()).hexdigest()
            url = f"{base_url}/{rel_path}"

            doc_files.append(DocFile(
                path=rel_path,
                url=url,
                content=content,
                content_hash=content_hash,
            ))

    return doc_files


def resolve_relative_links(rel_path: str, base_url: str, content: str) -> str:
    links = link_pattern.findall(content)
    for _, url, _ in links:
        if not relative_path_pattern.match(url):
            continue

        current_dir = os.path.dirname(rel_path)
        new_url = f"{base_url}/{current_dir}/{url}"
        content = content.replace(url, new_url)

    return content
