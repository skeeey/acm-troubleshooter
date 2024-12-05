#!/usr/bin/env bash

# list runbook repos
curl -s -X GET 127.0.0.1:8000/runbooksets

# add and index runbooks
curl -s -X PUT --header "Content-Type: application/json" \
    127.0.0.1:8000/runbooksets \
    -d '{"repo": "https://github.com/skeeey/foundation-docs.git", "branch": "test"}')


# get a runbook repo with its indexed version 
# curl -s -X GET $api_host/runbooksets/${runbook_set_id}


# delete a runbook repo
# curl -s -X DELETE $api_host/runbooksets/${runbook_set_id}
