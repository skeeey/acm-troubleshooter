SHELL:=/bin/bash

.PHONY: deps
deps:
	pip install -r requirements.txt

.PHONY: run-server
run-server:
	hack/run_server.sh

.PHONY: run-streamlit
run-streamlit:
	hack/run_streamlit.sh
