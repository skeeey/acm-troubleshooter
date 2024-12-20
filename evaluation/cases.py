# coding: utf-8

"""
The cases for index evaluation
"""

irrelevant_cases = [
    "hello",
    "hello world",
    "dfs",
    "leo",
    "get the answer",
]

cluster_cases = [
    "troubleshoot why the status of the cluster cluster-a is unknown",
    # "cluster unknown",
    # "cluster is unknown",
    # "cluster status is unknown",
    # "why cluster is unknown",
    # "why cluster status is unknown",
    # "my cluster local-cluster is unknown",
    # "My cluster stuck in the Installing state when I install multicluster
    # engine operator on a OpenShift Service on AWS with hosted control planes cluster",
    # "The status of all managed clusters on a OpenShift Service on AWS hosted
    # clusters suddenly becomes Unknown.",
]

addon_cases = [
    "troubleshoot why my addon work-manager is missing in my cluster cluster-b",
    "my addons are missing on the managed clusters",
    "my addons are missing in the managed clusters",
    "my addons are missing in the clusters",
    "my addon work-manager is missing in my cluster",
    "the work-manager addon is not running on the cluster1",
    "Why the add-on namespace is leftover during the cluster detaching process?"
]

question_cases = [
    # "what's the acm?",
    "what's the policy?",
    # "what's the application?",
    # "what's the globalhub",
    # "what's the multicluster global hub?",
    # "how to access acm",
    # "How to get must-gather for global hub",
    # "How to resolve ERROR: could not resize shared memory segment \"/PostgreSQL.1083654800\" to
    # 25031264 bytes: No space left on device (SQLSTATE 53100)",
]

negative_cases = [
    "cluster status is unkown",
    "cluster status is unknow",
    "cluster status is unknon",
    "cluster unknow",
    "why the cluster status is unknow?",
    "why the clsuter status is unknown",
    "my cluster is unkonwn",
    "my cluster local-cluster is unkown",
    "my cluster local-cluster is unknow",
]
