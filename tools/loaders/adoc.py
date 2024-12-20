# coding: utf-8

"""
Load adoc files
"""

import os
import logging
import shutil
from llama_index.core.schema import Document
from tools.common import run_commands
from tools.loaders.helper import list_files, to_docs

acm_docs_attrs = {
  "aap": "Red Hat Ansible Automation Platform",
  "aap-short": "Ansible Automation Platform",
  "ai": "Assisted Installer",
  "ibio": "Image Based Install Operator",
  "update-service": "OpenShift Update Service",
  "global-hub": "multicluster global hub",
  "gate": "Gatekeeper operator",
  "mce": "multicluster engine for Kubernetes operator",
  "mce-short": "multicluster engine operator",
  "ocp": "Red Hat OpenShift Container Platform",
  "ocp-short": "OpenShift Container Platform",
  "ocp-virt": "Red Hat OpenShift Virtualization",
  "ocp-virt-short": "OpenShift Virtualization",
  "olm": "Operator Lifecycle Manager",
  "ocm": "OpenShift Cluster Manager",
  "rosa": "OpenShift Service on AWS",
  "acm": "Red Hat Advanced Cluster Management for Kubernetes",
  "acm-short": "Red Hat Advanced Cluster Management",
  "product-version": "2.12",
  "mce-version": "2.7",
  "product-version-prev": "2.11",
  "quay": "Red Hat Quay",
  "quay-short": "Quay",
  "imagesdir": "../images",
  "sno": "single-node OpenShift",
  "sco": "SiteConfig operator",
  "gitops": "Red Hat OpenShift GitOps",
  "gitops-short": "OpenShift GitOps",
  "cim": "central infrastructure management",
  "infra": "infrastructure operator for Red Hat OpenShift"
}

logger = logging.getLogger(__name__)

def convert_adoc_to_md(adoc_file, output_file):
    cmds = ["npx", "downdoc", "--output", output_file, adoc_file]
    convert_result = run_commands(cmds=cmds, cwd=None, timeout=120)
    if convert_result.return_code != 0:
        raise RuntimeError(f"failed to convert adoc docs, {convert_result.stderr}")

def mk_output_dir(output_dir):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)

def load_acm_docs(adoc_dir: str, source: str, exclude_list=None) -> list[Document]:
    if exclude_list is None:
        exclude_list = ["apis", "api", "README.adoc", "SECURITY.adoc", "EXTERNAL_CONTRIBUTING.adoc",
                        ".asciidoctorconfig.adoc", "common-attributes.adoc", "main.adoc", "master.adoc"]

    parent_dir = os.path.dirname(adoc_dir)
    md_dir = os.path.join(parent_dir, f"{os.path.basename(adoc_dir)}-md")

    # prepare markdown output dir
    mk_output_dir(md_dir)

    # convert adoc to markdown
    for f in list_files(adoc_dir, exclude_list, ".adoc"):
        logger.info("convert adoc %s", f)
        convert_adoc_to_md(f, os.path.join(md_dir, f.replace(adoc_dir, "").replace("/", "_")[1:]) + ".md")

    mce_troubleshooting_docs = set()
    acm_troubleshooting_docs = set()
    acm_docs = set()

    # classify the docs
    for f in list_files(md_dir, [], ".md"):
        fname = os.path.basename(f)

        if "troubleshooting" in os.path.basename(fname):
            if "troubleshooting_intro" in fname:
                continue

            if fname.startswith("clusters_support_"):
                mce_troubleshooting_docs.add(f)
                continue

            acm_troubleshooting_docs.add(f)
            continue

        acm_docs.add(f)

    # remove the repetitive docs
    for f in mce_troubleshooting_docs:
        name = f.replace("clusters_support_", "").replace("_mce", "")
        if "must_gather" in name:
            continue

        if name in acm_troubleshooting_docs:
            acm_troubleshooting_docs.remove(name)

    docs = []
    docs.extend(to_docs(mce_troubleshooting_docs, source, acm_docs_attrs))
    docs.extend(to_docs(acm_troubleshooting_docs, source, acm_docs_attrs))
    docs.extend(to_docs(acm_docs, source, acm_docs_attrs, True))
    return docs
