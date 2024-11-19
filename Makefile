SHELL:=/bin/bash

.PHONY: deps
deps:
	pip install -r requirements.txt

.PHONY: binary
binary:
	hack/build_binary.sh
