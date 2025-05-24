#!/usr/bin/env bash

# add and index document repos
curl -v -X POST --header "Content-Type: application/json" \
    127.0.0.1:8000/api/documents/ \
    -d '{"repo":"https://github.com/stolostron/foundation-docs.git","branch":"main","desc":"the runbooks for server foundation, these runbooks are used for troubleshooting managedcluster, manifestwork, managedclsuteraddon problems"}'

curl -v -X POST --header "Content-Type: application/json" \
    127.0.0.1:8000/api/documents/ \
    -d '{"repo":"https://github.com/stolostron/rhacm-docs.git","branch":"2.13_prod","desc":"Red Hat Advanced Cluster Management for Kubernetes documentation"}'

# list document repos
curl -s -X GET 127.0.0.1:8000/api/documents/

# get a document repo with its id
curl -s -X GET 127.0.0.1:8000/api/documents/${document_id}

# delete a document repo
curl -s -X DELETE 127.0.0.1:8000/api/documents/${document_id}

# retrieve documents for a query
curl -s -X POST --header "Content-Type: application/json" \
    127.0.0.1:8000/api/documents/retrieve \
    -d '{"query": "troubleshoot why the status of my cluster cluster-a is unknown"}'
