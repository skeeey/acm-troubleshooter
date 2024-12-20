#!/usr/bin/env bash

api_host="127.0.0.1:8000"

# start to troubleshoot an issue
resp=$(curl -s -X POST --header "Content-Type: application/json" \
    $api_host/chat/ \
    -d '{"query": "my cluster local-cluster is unknown"}')
echo $resp

issue_id=$(echo $resp | jq -r '.issue_id')

# continue to troubleshoot the issue
resp=$(curl -s -X POST --header "Content-Type: application/json" \
    $api_host/chat/ \
    -d '{"issue_id": "'$issue_id'", "query": "the ManagedClusterConditionAvailable is Unknown; the ManagedClusterImportSucceeded is True"}')
echo $resp

resp_id=$(echo $resp | jq -r '.resp_id')

# evaluate the response
curl -s -X PUT --header "Content-Type: application/json" \
    $api_host/evaluation/ \
    -d '{"issue_id": "'$issue_id'", "resp_id": "'$resp_id'", "score": 1}'

# continue ...
