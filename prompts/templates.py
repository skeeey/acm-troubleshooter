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
- Terms "global-hub", "globalhub" or "global hub" stands for multicluster global hub.
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

# TODO using a grace prompt to stop the troubleshooting process
REPLAN_NOTICES = """
If the new plan contains `oc apply` command, Set the termination to true, otherwise set it to false.
"""

EXECUTOR_EXAMPLES = """
  Current Plan:
    Check the ManagedClusterConditionAvailable condition for managed cluster cluster1 on the hub cluster:
    ```sh
    oc get managedcluster cluster1 -ojsonpath='{.status.conditions[?(@.type=="ManagedClusterConditionAvailable")].status}'
    ```
  Output Commands:
    omc use /home/user1/hub
    available_status=$(omc get managedcluster cluster1 -ojsonpath='{.status.conditions[?(@.type=="ManagedClusterConditionAvailable")].status}')
    echo "ManagedClusterConditionAvailable for cluster1: ${available_status}"
"""
