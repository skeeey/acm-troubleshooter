# coding: utf-8

"""
Help to load markdown files
"""

import logging
import os
import re
import shutil
from pathlib import Path
from server.tools.loaders.common import link_pattern, list_files, DocLocation

logger = logging.getLogger(__name__)

relative_path_pattern = re.compile(r"^(?:\.{1,2}/)+")

def convert_mds(doc_dir: str,
                 base_url: str,
                 exclude_list: list[str] = None) -> list[DocLocation]:
    if exclude_list is None:
        exclude_list = ["README.md", "SECURITY.md", "GUIDELINE.md", "index.md"]

    parent_dir = os.path.dirname(doc_dir)
    md_dir = os.path.join(parent_dir, f"{os.path.basename(doc_dir)}-overwrite")

    # prepare output dir
    if Path(md_dir).exists():
        shutil.rmtree(md_dir)
    Path(md_dir).mkdir()

    runbooks = []
    for rb_f in list_files(doc_dir, exclude_list, ".md"):
        with open(Path(rb_f), encoding="utf-8") as f:
            content = f.read()

        content = replace_inline_links(Path(rb_f.replace(doc_dir, "")), base_url, content)

        # overwrite the file
        output_file = rb_f.replace(doc_dir, md_dir)
        Path(os.path.dirname(output_file)).mkdir(parents=True, exist_ok=True)
        with open(Path(output_file), "w", encoding="utf-8") as f:
            f.write(content)

        url = f"{base_url}{Path(rb_f.replace(doc_dir, ""))}"
        runbooks.append(DocLocation(path=output_file, url=url))

    return runbooks

def replace_inline_links(current_path: Path, base_url: str, content: str) -> str:
    links = re.findall(link_pattern, content)
    for text, url, _ in links:
        logger.debug("replace the link: [%s](%s)", text, url)
        if not relative_path_pattern.match(url):
            logger.debug("ignore the link: [%s](%s)", text, url)
            continue

        current_dir = os.path.dirname(current_path)
        new_url = f"{base_url}{current_dir}/{url}"
        content = content.replace(url, new_url)

    return content