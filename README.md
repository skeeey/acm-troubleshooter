## Prepare

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

3. Instal [`omc` command](https://github.com/gmeghnag/omc)

## Diagnose an ACM issue with runbooks and must-gather

```sh
# For example:
# - Using groq https://console.groq.com llama-3.1-70b-versatile
#   export LM_MODEL=llama-3.1-70b-versatile
#   export LM_API_BASE=https://api.groq.com/openai/v1
#   export LM_API_KEY=<your-groq-api-key>
# - Using ollama/qwen2.5:32b
#   export LM_MODEL=ollama/qwen2.5:32b
#   export LM_API_BASE=http://localhost:11434
export LM_MODEL=<your-lm-model>
export LM_API_BASE=<your-lm-api> 
export LM_API_KEY=<your-lm-api-key>

python -m apps.troubleshooter --runbooks=<your-runbooks-dir> \
    --hub-mg=<your-hub-must-gather-dir> \
    --cluster-mg=<your-managed-cluster-must-gather-dir> \
    <your-issue>
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

## Refers to
- https://github.com/stanfordnlp/dspy
- https://github.com/langchain-ai/langgraph
- https://github.com/gmeghnag/omc
- https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/plan-and-execute/
