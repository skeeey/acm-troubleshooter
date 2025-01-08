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
make local/run-server
```

4. Add docs

```sh
curl -s -X PUT --header "Content-Type: application/json" 127.0.0.1:8000/runbooksets \
    -d '{"repo": "https://github.com/stolostron/foundation-docs.git", "branch": "main"}'
```

5. Run the web UI service

```sh
make local/run-streamlit
```

## Runbook Guideline

For a runbook, it should

1. Give a title for the runbook, the title summarizes the issue that this runbook aims to diagnosis.
2. Clearly and detailedly describe the issue, for example
    - describe the issue's symptom, for example, the condition status of a resource when the issue happens, the error message, etc;
    - describe why this issue happens and which components or resources will be impacted when this issue happens, etc.
3. Clearly and detailedly describe describe the diagnosis steps, for example
    - list the diagnosis steps one-by-one;
    - specify whether the step should be run on the hub cluster or the managed cluster;
    - if one step needs to refer to the other runbooks, using the related runbook title as the markdown link text, for example, `[runbook_title](runbook_location)`

## TODO
- [x] support to ask ACM relevant questions/knowledge
- [x] support to evaluate the response by user
- [x] support to show current used docs in UI
- [ ] continue to test the result with real user issues (slack/customer cases)
- [ ] issue triage (determine which team is responsible for the issue)
- [ ] generate a slack bot in the mce/server-foundation channel
- [ ] use a local LLM
- [ ] the retrieve results evaluation standard
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
