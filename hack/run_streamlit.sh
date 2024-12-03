#!/usr/bin/env bash

REPO_DIR="$(cd "$(dirname ${BASH_SOURCE[0]})/.." ; pwd -P)"

output_dir=${REPO_DIR}/_output
log_dir=${output_dir}/logs

mkdir -p ${log_dir}

date_suffix=$(date +"%Y%m%d%H%M%S")

(exec streamlit --server.address 0.0.0.0 --server.port 80 run ${REPO_DIR}ui/app.py) &> ${log_dir}/streamlit.${date_suffix}.log &
streamlit_pid=$!
echo "$streamlit_pid" > ${output_dir}/"streamlit_pid.${date_suffix}"
echo "streamlit ($streamlit_pid) is running ..."
echo "log is located at ${log_dir}/streamlit_pid.${date_suffix}.log"
