## Run services locally

1. Create a virtual environment

```sh
VENV=<your-python-virtual-environment-dir> # e.g. $HOME/acm-troubleshooter/.venv
mkdir -p $VENV
python -m venv $VENV
source $VENV/bin/activate
```

2. Install dependents

```sh
make deps
```

3. Run the RESTful service

```sh
make install-downdoc
make run-pgvector
make local/run-server
```

4. Run the web UI service

```sh
make local/run-streamlit
```

## TODO
- [x] support to ask ACM relevant questions/knowledge
- [x] support to evaluate the response by user
- [x] support to show current used docs in UI
- [ ] continue to test with real user issues (slack/customer cases)
- [ ] issue triage (determine which team is responsible for the issue)
- [ ] generate a slack bot in the mce/server-foundation channel
- [ ] use a local LLM
- [x] the retrieve results evaluation standard
- [ ] the LLM response evaluation standard

## Refers to
- https://github.com/stanfordnlp/dspy/
- https://docs.streamlit.io/
- https://docs.llamaindex.ai/en/stable/
- https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5
- https://github.com/langchain-ai/langgraph/
- https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/
- https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/plan-and-execute/
- https://huggingface.co/spaces/mteb/leaderboard
