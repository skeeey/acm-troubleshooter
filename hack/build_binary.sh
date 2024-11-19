#!/bin/bash

set -e

PWD="$(cd "$(dirname ${BASH_SOURCE[0]})" ; pwd -P)"
ROOT_DIR="$(cd ${PWD}/.. && pwd -P)"

# make sure the pyinstaller is installed
pip install -U pyinstaller

# clean up
rm -rf $ROOT_DIR/_output $ROOT_DIR/build $ROOT_DIR/dist $ROOT_DIR/troubleshooter.spec

mkdir -p $ROOT_DIR/_output

# build binary
pyinstaller --hidden-import=tiktoken_ext.openai_public --hidden-import=tiktoken_ext apps/troubleshooter.py
mkdir -p ${ROOT_DIR}/dist/troubleshooter/_internal/litellm/llms/tokenizers
echo "{}" > ${ROOT_DIR}/dist/troubleshooter/_internal/litellm/llms/tokenizers/anthropic_tokenizer.json

pushd $ROOT_DIR/dist/troubleshooter
tar -zcf $ROOT_DIR/_output/acm-troubleshooter.tar.gz *
popd
