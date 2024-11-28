#!/usr/bin/env bash

REPO_DIR="$(cd "$(dirname ${BASH_SOURCE[0]})/.." ; pwd -P)"

output_dir=${REPO_DIR}/_output
log_dir=${output_dir}/logs

mkdir -p ${log_dir}

date_suffix=$(date +"%Y-%m-%dT%H:%M.%S")

(exec uvicorn server.main:app --host 0.0.0.0 --port 8000) &> ${log_dir}/server.${date_suffix}.log &
server_pid=$!
echo "$server_pid" > ${output_dir}/"server_pid.${date_suffix}"
echo "server ($server_pid) is running ..."
echo "log is located at ${log_dir}/server.${date_suffix}.log"
