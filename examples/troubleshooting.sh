#!/usr/bin/env bash

api_host="127.0.0.1:8000"

# start to troubleshoot an issue
resp=$(curl -s -X PUT --header "Content-Type: application/json" \
    $api_host/issues \
    -d '{"issue": "my cluster local-cluster is unknown"}')
echo $resp

issue_id=$(echo $resp | jq -r '.issue_id')
last_step_id=$(echo $resp | jq -r '.step_id')

# evaluate the troubleshooting plan
curl -s -X PUT --header "Content-Type: application/json" \
    $api_host/issues/${issue_id}/evaluation/${last_step_id} \
    -d '{"score": 1}'

# continue to troubleshoot the issue
resp=$(curl -s -X POST --header "Content-Type: application/json" \
    $api_host/issues/$issue_id \
    -d '{"last_step_id": "'$last_step_id'", "results": "the ManagedClusterConditionAvailable is Unknown; the ManagedClusterImportSucceeded is True"}')
echo $resp

issue_id=$(echo $resp | jq -r '.issue_id')
last_step_id=$(echo $resp | jq -r '.step_id')

# evaluate the troubleshooting plan
curl -s -X PUT --header "Content-Type: application/json" \
    $api_host/issues/${issue_id}/evaluation/${last_step_id} \
    -d '{"score": -1}'

# continue ...
