#!/usr/bin/env bash

REPO_DIR="$(cd "$(dirname ${BASH_SOURCE[0]})/.." ; pwd -P)"

data_dir="${HOME}/acm-docs-postgres-data"
pgvector_img="pgvector/pgvector:pg16"
pgvector_pw=$(LC_CTYPE=C tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c 16)

mkdir -p $data_dir
echo "$pgvector_pw" > $REPO_DIR/pgvector.password

podman rm psql-acm -f

podman run --name psql-acm -p 5432:5432 \
    -e POSTGRES_DB=acm -e POSTGRES_USER=acm -e POSTGRES_PASSWORD=${pgvector_pw} \
    -v $data_dir:/var/lib/postgresql/data:z \
    -d $pgvector_img

sleep 1

podman ps
