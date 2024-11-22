#!/usr/bin/env bash

set -e

PWD="$(cd "$(dirname ${BASH_SOURCE[0]})" ; pwd -P)"
ROOT_DIR="$(cd ${PWD}/.. && pwd -P)"

# make sure the pyinstaller is installed
pip install -U pyinstaller

# clean up
rm -rf $ROOT_DIR/_output $ROOT_DIR/build $ROOT_DIR/dist $ROOT_DIR/troubleshooter.spec

mkdir -p $ROOT_DIR/_output

# required files
litellm_location=$(pip show litellm | grep Location | awk '{print $2}')
unstructured_location=$(pip show unstructured | grep Location | awk '{print $2}')
emoji_location=$(pip show emoji | grep Location | awk '{print $2}')

# build binary
pyinstaller --add-data "$litellm_location/litellm/llms/tokenizers/anthropic_tokenizer.json:./litellm/llms/tokenizers" \
    --add-data "$unstructured_location/unstructured/nlp/english-words.txt:./unstructured/nlp" \
    --add-data "$emoji_location/emoji/unicode_codes:./emoji/unicode_codes" \
    --hidden-import=tiktoken_ext.openai_public \
    --hidden-import=tiktoken_ext \
    apps/troubleshooter.py

pushd $ROOT_DIR/dist/troubleshooter
tar -zcf $ROOT_DIR/_output/acm-troubleshooter-$(uname)-$(uname -m).tar.gz *
popd
