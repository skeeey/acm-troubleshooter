# coding: utf-8

DSPY_PLANNER_NOTICES = """
- The term "hub" always refers to the ACM Hub.
- The term "addon" always refers to the ACM ManagedClusterAddOn.
- Terms like "cluster", "managed cluster", "spoke", "spoke cluster", or "ManagedCluster" refer to an ACM managed cluster.
- Use the cluster name in the plan.
- Use the addon name in the plan.
"""

DSPY_EXECUTOR_RULES = """
- Only identify the cause of the issue.
- Do not solve the problem.
- Do not generate conditional statements in commands.
- Use omc instead of oc or kubectl.
- If the commands will run in the hub cluster, use omc use <hub_must_gather_dir>.
- If the commands will run in a managed cluster, initialize the omc command with `omc use <spoke_must_gather_dir>`.
"""

DSPY_EXECUTOR_EXAMPLES = """
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

DSPY_REPLAN_NOTICES = """
If the new plan contains `oc apply` command, Set the termination to true, otherwise set it to false.
"""
