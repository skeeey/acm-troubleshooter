SHELL:=/bin/bash

.PHONY: deps
deps:
	pip install -r requirements.txt

.PHONY: binary
binary:
	hack/build_binary.sh

.PHONY: run
run:
	hack/run_server.sh


.PHONY: service
service:
	streamlit run ui/app.py