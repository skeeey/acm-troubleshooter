SHELL:=/bin/bash

.PHONY: deps
deps:
	pip install -r requirements.txt

.PHONY: lint
lint:
	pylint **/*.py

.PHONY: run-pgvector
run-pgvector:
	hack/run_pgvector.sh

.PHONY: run-server
run-server:
	hack/run_server.sh

.PHONY: run-streamlit
run-streamlit:
	hack/run_streamlit.sh

.PHONY: local/run-server
local/run-server:
	uvicorn server.main:app

.PHONY: local/run-streamlit
local/run-streamlit:
	streamlit run --server.port=8080 ui/main.py

.PHONY: local/run-mlflow
local/run-mlflow:
	mlflow ui --port 5000
