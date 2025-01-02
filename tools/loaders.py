# coding: utf-8

"""
Help to load doc files
"""

import os
import logging
import shutil
import re
import hashlib
from pathlib import Path
from llama_index.core.schema import Document
from llama_index.readers.file import FlatReader
from llama_index.readers.file import MarkdownReader
from models.docs import DocLocation
from tools.common import run_commands
from tools.common import count_tokens

logger = logging.getLogger(__name__)

link_pattern = r"\[([^\]]+)\]\(([^ )]+)(?: \"([^\"]+)\")?\)"
anchor_pattern = re.compile(r"#(?P<anchor>[^)]+)")
relative_path_pattern = re.compile(r"^(?:\.{1,2}/)+")

def list_files(start_path, exclude_list, suffix):
    file_list = []
    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if not d == ".git"]

        if os.path.basename(root) in exclude_list:
            continue

        for f in files:
            if f.endswith(suffix) and f not in exclude_list:
                file_list.append(os.path.join(root, f))

    return file_list

def get_first_path(current_path: Path) -> str:
    if len(current_path.parts) <= 1:
        raise ValueError(f"bad path: {current_path}")

    return current_path.parts[1]

def get_acm_component_path(current_path: Path) -> str:
    component_name = get_first_path(current_path)
    # TODO find the mapping from main.adoc
    if component_name == "console":
        return "web_console/index"

    if component_name == "global_hub":
        return "multicluster_global_hub/index"

    if component_name == "mce_acm_integration":
        return "multicluster_engine_operator_with_red_hat_advanced_cluster_management/index"

    return f"{component_name}/index"

def to_acm_url(current_path: Path, base_url: str, url: str):
    component_path = get_acm_component_path(current_path)

    match = anchor_pattern.search(url)
    if not match:
        return f"{base_url}/{component_path}"

    anchor = match.group('anchor').strip()
    return f"{base_url}/{component_path}#{anchor}"

def replace_acm_doc_inline_links(current_path: Path, base_url: str, content: str) -> str:
    links = re.findall(link_pattern, content)
    for text, url, _ in links:
        logger.debug("replace the link: [%s](%s)", text, url)
        if url.startswith("./"):
            new_url = to_acm_url(current_path, base_url, url)
            content = content.replace(url, new_url)
            continue

        if url.startswith("../../"):
            new_url = to_acm_url(Path(url.replace("../..", "")), base_url, url)
            content = content.replace(url, new_url)
            continue

        if url.startswith("../images"):
            # TODO handle image links
            continue

        if url.startswith("../"):
            new_url = to_acm_url(Path(url.replace("..", "")), base_url, url)
            content = content.replace(url, new_url)
            continue

    return content

def remove_acm_repetitive_docs(docs: list[str]) -> list[str]:
    acm_docs = []
    mce_troubleshooting_docs = set()
    acm_troubleshooting_docs = set()

    for f in docs:
        if "support_troubleshooting" in f:
            mce_troubleshooting_docs.add(f)
            continue

        if "troubleshooting" in f:
            acm_troubleshooting_docs.add(f)
            continue

        acm_docs.append(f)

    for f in mce_troubleshooting_docs:
        name = f.replace("clusters/support_troubleshooting", "troubleshooting").replace("_mce", "")
        if "must_gather" in name:
            continue

        if "troubleshooting_intro" in name:
            continue

        if name in acm_troubleshooting_docs:
            logger.debug("remove repetitive doc: %s", name)
            acm_troubleshooting_docs.remove(name)

    acm_docs.extend(mce_troubleshooting_docs)
    acm_docs.extend(acm_troubleshooting_docs)
    return acm_docs

def get_acm_doc_link(base_url: str, parent_dir: str, file_path: str):
    component_path=get_acm_component_path(Path(file_path.replace(parent_dir, "")))
    adoc_f = file_path.replace("-md", "").replace(".md", "")
    with open(adoc_f, 'r', encoding='utf-8') as f:
        anchor = next(f).strip().removeprefix("[").removesuffix("]")
        url = f"{base_url}/{component_path}{anchor}"
    return url

def convert_acm_docs(adoc_dir: str, doc_attrs: dict[str, str], base_url: str, exclude_list: list[str]) -> list[DocLocation]:
    parent_dir = os.path.dirname(adoc_dir)
    md_dir = os.path.join(parent_dir, f"{os.path.basename(adoc_dir)}-md")
    md_files = []

    # prepare markdown output dir
    if Path(md_dir).exists():
        shutil.rmtree(md_dir)
    Path(md_dir).mkdir()

    # convert adoc to markdown
    logger.info("convert acm docs...")
    for f in list_files(adoc_dir, exclude_list, ".adoc"):
        output_file = f.replace(adoc_dir, md_dir) + ".md"
        Path(os.path.dirname(output_file)).mkdir(parents=True, exist_ok=True)
        logger.debug("convert adoc %s to %s", f, output_file)
        cmds = ["npx", "downdoc", "--output", output_file, f]
        convert_result = run_commands(cmds=cmds, cwd=None, timeout=120)
        if convert_result.return_code != 0:
            raise RuntimeError(f"failed to convert adoc docs, {convert_result.stderr}")
        md_files.append(output_file)
    logger.info("convert acm docs (done)")

    for md_f in md_files:
        with open(Path(md_f), encoding="utf-8") as f:
            content = f.read()

        # replace doc attrs
        for key in doc_attrs:
            content = content.replace("{"+key+"}", doc_attrs[key])

        # replace plus sign line
        content = re.sub(r"^\+$", "", content, flags=re.MULTILINE)

        # replace inline links
        content = replace_acm_doc_inline_links(Path(md_f.replace(md_dir, "")), base_url, content)

        # overwrite the file
        with open(Path(md_f), "w", encoding="utf-8") as f:
            f.write(content)

    # remove the repetitive docs
    acm_docs = []
    acm_doc_files = remove_acm_repetitive_docs(md_files)
    for doc_f in acm_doc_files:
        url = get_acm_doc_link(base_url, md_dir, doc_f)
        acm_docs.append(DocLocation(path=doc_f, url=url))
    return acm_docs

def replace_runbook_inline_links(current_path: Path, base_url: str, content: str) -> str:
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

def overwrite_runbooks(rb_dir: str, base_url: str, exclude_list: list[str]) -> list[DocLocation]:
    parent_dir = os.path.dirname(rb_dir)
    md_dir = os.path.join(parent_dir, f"{os.path.basename(rb_dir)}-overwrite")

    # prepare output dir
    if Path(md_dir).exists():
        shutil.rmtree(md_dir)
    Path(md_dir).mkdir()

    runbooks = []
    for rb_f in list_files(rb_dir, exclude_list, ".md"):
        with open(Path(rb_f), encoding="utf-8") as f:
            content = f.read()
        
        content = replace_runbook_inline_links(Path(rb_f.replace(rb_dir, "")), base_url, content)

        # overwrite the file
        output_file = rb_f.replace(rb_dir, md_dir)
        Path(os.path.dirname(output_file)).mkdir(parents=True, exist_ok=True)
        with open(Path(output_file), "w", encoding="utf-8") as f:
            f.write(content)

        url = f"{base_url}{Path(rb_f.replace(rb_dir, ""))}"
        runbooks.append(DocLocation(path=output_file, url=url))

    return runbooks

def to_docs(files: list[DocLocation], source: str, chunk_limit=2048) -> list[Document]:
    docs = []
    for f in files:
        doc = FlatReader().load_data(Path(f.path))[0]

        tokens = count_tokens(doc.text)
        if tokens > chunk_limit:
            # TODO need a better way to handle this
            logger.info("partition the large docs %s (tokens=%d)", f, tokens)
            docs.extend(do_partition(f, source))
            continue

        # override the metadata
        doc.metadata = {
            "filename": f.path,
            "filelink": f.url,
            "hash": hashlib.md5(doc.text.encode()).hexdigest(),
            "source": source,
        }

        docs.append(doc)
    return docs

def do_partition(f: DocLocation, source: str) -> list[Document]:
    docs = MarkdownReader().load_data(Path(f.path))
    for doc in docs:
        doc.metadata = {
            "filename": f.path,
            "filelink": f.url,
            "hash": hashlib.md5(doc.text.encode()).hexdigest(),
            "source": source,
        }
    return docs
