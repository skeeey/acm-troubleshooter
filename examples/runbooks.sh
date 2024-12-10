#!/usr/bin/env bash

# list runbook repos
curl -s -X GET 127.0.0.1:8000/runbooksets

# add and index runbooks
curl -X POST --header "Content-Type: application/json" \
    127.0.0.1:8000/runbooksets \
    -d '{"repo": "https://github.com/stolostron/foundation-docs.git", "branch": "main"}'


# get a runbook repo with its indexed version 
# curl -s -X GET $api_host/runbooksets/${runbook_set_id}


# delete a runbook repo
# curl -s -X DELETE $api_host/runbooksets/${runbook_set_id}
