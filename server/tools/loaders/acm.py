# coding: utf-8

"""
Help to load acm adoc files
"""

import logging
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from pydantic import BaseModel
from server.tools.cmd import run_commands
from server.tools.loaders.common import link_pattern, list_files, DocLocation

logger = logging.getLogger(__name__)

acm_url="https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.12/html-single"
anchor_pattern = re.compile(r"#(?P<anchor>[^)]+)")

class Task(BaseModel):
    in_f: str
    out_f: str

def convert_docs(doc_dir: str,
                 max_workers = 50,
                 base_url: str = acm_url,
                 exclude_list: list[str] = None) -> list[DocLocation]:
    if exclude_list is None:
        exclude_list = ["apis", "api", "README.adoc", "SECURITY.adoc", "EXTERNAL_CONTRIBUTING.adoc",
                        ".asciidoctorconfig.adoc", "common-attributes.adoc", "main.adoc", "master.adoc"]

    parent_dir = os.path.dirname(doc_dir)
    md_dir = os.path.join(parent_dir, f"{os.path.basename(doc_dir)}-md")
    md_files = []

    # prepare markdown output dir
    if Path(md_dir).exists():
        shutil.rmtree(md_dir)
    Path(md_dir).mkdir()

    # convert adoc to markdown
    # TODO consider to use asciidoc directly
    tasks = []
    for adoc_f in list_files(doc_dir, exclude_list, ".adoc"):
        md_f = adoc_f.replace(doc_dir, md_dir) + ".md"
        Path(os.path.dirname(md_f)).mkdir(parents=True, exist_ok=True)
        tasks.append(Task(in_f=adoc_f, out_f=md_f))
        md_files.append(md_f)

    logger.info("convert acm docs (%d) ...", len(tasks))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(convert_adoc_to_md, task) for task in tasks]
        for future in as_completed(futures):
            future.result()
    logger.info("convert acm docs (done)")

    doc_attrs = get_doc_attrs(os.path.join(doc_dir, "modules", "common-attributes.adoc"))

    for md_f in md_files:
        with open(Path(md_f), encoding="utf-8") as f:
            content = f.read()

        # replace doc attrs
        for key in doc_attrs:
            content = content.replace("{"+key+"}", doc_attrs[key])

        # replace plus sign line
        content = re.sub(r"^\+$", "", content, flags=re.MULTILINE)

        # replace inline links
        content = replace_doc_inline_links(Path(md_f.replace(md_dir, "")), base_url, content)

        # overwrite the file
        with open(Path(md_f), "w", encoding="utf-8") as f:
            f.write(content)

    # remove the repetitive docs
    acm_docs = []
    acm_doc_files = remove_repetitive_docs(md_files)
    for doc_f in acm_doc_files:
        url = get_doc_link(base_url, md_dir, doc_f)
        acm_docs.append(DocLocation(path=doc_f, url=url))
    return acm_docs

def convert_adoc_to_md(task: Task):
    logger.debug("convert adoc %s to %s", task.in_f, task.out_f)
    cmds = ["npx", "downdoc", "--output", task.out_f, task.in_f]
    convert_result = run_commands(cmds=cmds, cwd=None, timeout=300)
    if convert_result.return_code != 0:
        raise RuntimeError(f"failed to convert adoc doc {task.in_f}, {convert_result.stderr}")

def replace_doc_inline_links(current_path: Path, base_url: str, content: str) -> str:
    links = re.findall(link_pattern, content)
    for text, url, _ in links:
        logger.debug("replace the link: [%s](%s)", text, url)
        if url.startswith("./"):
            new_url = to_url(current_path, base_url, url)
            content = content.replace(url, new_url)
            continue

        if url.startswith("../../"):
            new_url = to_url(Path(url.replace("../..", "")), base_url, url)
            content = content.replace(url, new_url)
            continue

        if url.startswith("../images"):
            # TODO handle image links
            continue

        if url.startswith("../"):
            new_url = to_url(Path(url.replace("..", "")), base_url, url)
            content = content.replace(url, new_url)
            continue

    return content

def to_url(current_path: Path, base_url: str, url: str):
    component_path = get_component_path(current_path)

    match = anchor_pattern.search(url)
    if not match:
        return f"{base_url}/{component_path}"

    anchor = match.group("anchor").strip()
    return f"{base_url}/{component_path}#{anchor}"

def get_component_path(current_path: Path) -> str:
    if len(current_path.parts) <= 1:
        raise ValueError(f"bad path: {current_path}")
    component_name = current_path.parts[1]
    # TODO find the mapping from main.adoc
    if component_name == "console":
        return "web_console/index"

    if component_name == "global_hub":
        return "multicluster_global_hub/index"

    if component_name == "mce_acm_integration":
        return "multicluster_engine_operator_with_red_hat_advanced_cluster_management/index"

    return f"{component_name}/index"

def remove_repetitive_docs(docs: list[str]) -> list[str]:
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

def get_doc_link(base_url: str, parent_dir: str, file_path: str):
    component_path=get_component_path(Path(file_path.replace(parent_dir, "")))
    adoc_f = file_path.replace("-md", "").replace(".md", "")
    with open(adoc_f, "r", encoding="utf-8") as f:
        anchor = next(f).strip().removeprefix("[").removesuffix("]")
        url = f"{base_url}/{component_path}{anchor}"
    return url

def get_doc_attrs(file_path) -> dict[str, str]:
    result_dict = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            parts = line.split(':', 2)
            if len(parts) == 3:
                key = parts[1].strip()
                value = parts[2].strip()
                result_dict[key] = value
    return result_dict

if __name__ == "__main__":
    convert_docs("/Users/wliu1/acm-docs/stolostron-rhacm-docs-2.13_prod")
