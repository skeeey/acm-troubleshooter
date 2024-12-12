#!/usr/bin/env bash

# list current runbook repos
curl -s -X GET 127.0.0.1:8000/runbooksets

# add and index a runbook repo
curl -v -X POST --header "Content-Type: application/json" \
    127.0.0.1:8000/runbooksets \
    -d '{"repo": "https://github.com/stolostron/foundation-docs.git", "branch": "main"}'


# get the runbook repo with its id
curl -s -X GET 127.0.0.1:8000/runbooksets/${runbook_set_id}


# delete the runbook repo
curl -s -X DELETE 127.0.0.1:8000/runbooksets/${runbook_set_id}
