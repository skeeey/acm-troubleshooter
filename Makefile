SHELL:=/bin/bash

.PHONY: deps
deps:
	pip install -r requirements.txt

.PHONY: binary
binary:
	hack/build_binary.sh

.PHONY: run-server
run-server:
	hack/run_server.sh

.PHONY: run-streamlit
run-streamlit:
	streamlit run ui/app.py