# coding: utf-8

"""
The task of indexing documents
"""

import logging
import os
import uuid
from services.index import RAGService
from services.storage import StorageService
from tools.loaders import convert_acm_docs, overwrite_runbooks, to_docs

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

def index(uid: uuid.UUID, repo_url: str, branch: str, version: str, repo_dir: str,
          rag_svc: RAGService, storage_svc: StorageService):
    rs = storage_svc.get_runbook_set(uid)
    if rs is None:
        logger.error("runbook set %s is not found", str(uid))
        return

    rsv = storage_svc.add_runbook_set_version(runbook_set_id=uid, version=version)

    source = f"{os.path.basename(repo_dir)}-{version}"
    logger.info("runbooks %s (%s) are indexing", source, version)
    docs = []
    if "rhacm-docs" in repo_dir:
        exclude_list = ["apis", "api", "README.adoc", "SECURITY.adoc", "EXTERNAL_CONTRIBUTING.adoc",
                    ".asciidoctorconfig.adoc", "common-attributes.adoc", "main.adoc", "master.adoc"]
        # TODO the version should be configured
        base_url = "https://docs.redhat.com/en/documentation/red_hat_advanced_cluster_management_for_kubernetes/2.12/html-single"
        docs.extend(convert_acm_docs(repo_dir, acm_docs_attrs, base_url, exclude_list))
    else:
        exclude_list = ["README.md", "SECURITY.md", "GUIDELINE.md", "index.md"]
        base_url = f"{repo_url.replace(".git", "")}/tree/{branch}"
        docs.extend(overwrite_runbooks(repo_dir, base_url, exclude_list))

    rag_svc.index_docs(to_docs(docs, source))

    rsv.state = "indexed"
    storage_svc.update_runbook_set_version(rsv)
    logger.info("runbooks %s (%s) were indexed", source, version)
