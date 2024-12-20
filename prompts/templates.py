# coding: utf-8

"""
The templates of prompt
"""

COMMON_NOTICES = """
- ACM or RHACM stands for Red Hat Advanced Cluster Management for Kubernetes.
- The term "hub" stands for to the ACM Hub.
- Terms like "cluster", "managed cluster", "spoke", "spoke cluster", or "ManagedCluster" stand for an ACM managed cluster.
- Terms "addon" or "add-on" stand for the ACM ManagedClusterAddOn.
- The term "mce" stands for multicluster engine operator.
- Terms "global-hub" or "global hub" stands for multicluster global hub.
- The term "ocp" stands for Red Hat OpenShift Container Platform.
- The term "ocm" stands for OpenShift Cluster Manager.
- The term "rosa" stands for OpenShift Service on AWS."""

RESPONSE_NOTICES = f"""
{COMMON_NOTICES}
- Use the cluster name in the response.
- Use the addon name in the response.
- Respond in Markdown format."""

CONVERTOR_NOTICES = f"""
{COMMON_NOTICES}
- The query should be about ACM.
- If the query is not related to ACM, return an empty string.
"""
