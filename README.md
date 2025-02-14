# LeanTool

A simple utility that connects LLMs with a "Code Interpreter" for Lean. This is implemented as *tool calls* from the LLM to the Lean executable, hence the name.

Current LLMs often have trouble with outputing correct Lean 4 syntax, due to the recent rapid changes in Lean. By allowing LLMs to talk directly to Lean, 
they are given opportunities to fix their mistakes.
Furthermore, Lean being an interactive theorem prover,
there are many interactive features that are not well represented in training data. 
This utility includes some initial efforts on prompting the LLMs with instructions on using these interactive features to better produce proofs.

Our design goal is to be flexible: easy to plug into automated workflows, but can also be plugged into human-facing chat/copilot interfaces.

This is part of a broader effort to create [safe and hallucination-free coding AIs](https://gasstationmanager.github.io/ai/2024/11/04/a-proposal.html). 


## Features

- Uses [LiteLLM](https://github.com/BerriAI/litellm) so you can plug in any compatible LLM, from OpenAI and Anthropic APIs to local LLMs hosted via ollama or vLLM.
- Feedback loop that allows the LLM to fix its errors.
- Uses [Pantograph](https://github.com/lenianiva/PyPantograph/) to extract goal states from `sorry`s.
- System prompt instructions to utilize Lean features that are likely missing from the LLMs' training data, including interactive commands that elicit suggestions / information from Lean
- Option to pass code in *plain text mode* instead of as tool calls formatted in JSON. This allows LeanTool
to be used by models that do not yet support tool/function calls, including
some reasoning models like Deepseek r1 and Gemini-2-flash-thinking.
- Plugin system to allow optional features to be included at run time.
- Flexible usage: as python library, as command-line chat interface, or as OpenAI-compatible API server

## API Server Demo

A demo of the OpenAI-compatible API server is up at [http://www.codeproofarena.com:8800/v1](http://www.codeproofarena.com:8800/v1).
To use it, connect your app to the above URL as the API Base URL, "provider" as OpenAI or OpenAI-compatible,
"model" as one of the key names in the models dict in [leantool.py](https://github.com/GasStationManager/LeanTool/blob/main/leantool.py),
and API key as your API key for the chosen model. See below for specific set up details for OpenWebUI, Continue.dev and Cline.

## Installation

- Install Lean
- Install `poetry`
- Clone the repository
- Install [Pantograph](https://github.com/lenianiva/PyPantograph/) by following its instructions. Create the wheel file. 
- Modify `pyproject.toml` in the LeanTool directory, to ensure the `pantograph` entry points to the correct path and file name to the `.whl` file.
- `poetry install`
- Install Mathlib as needed
- Set up your LLM model to connect via `LiteLLM`. E.g. for OpenAI, just set the environmental variable `OPENAI_API_KEY`. 
  For Anthropic, `ANTHROPIC_API_KEY`. If you want to try many different models, sign  up for an [OpenRouter](https://openrouter.ai/)
  API key and set `OPENROUTER_API_KEY`. For local models served by ollama, start by installing ollama. 
  See [Relevant LiteLLM Docs](https://docs.litellm.ai/docs/providers) for more detailed instructions. 
  The `models` dict in `leantool.py` has some preset models; it has the format "short name" : "LiteLLM model name". Modify it to have an entry for your model 
  if you have something different.

## Files

- `leantool.py` Python library. Simply import the file and call `interactive_lean_check` to invoke the feedback loop.
Currently used by [FormalizeWithTest](https://github.com/GasStationManager/FormalizeWithTest) autoformalization project,
and [WakingUp](https://github.com/GasStationManager/WakingUp) experiments on hallucination  detection.
- `cli_chat.py` command line chat interface.
- `app.py` Streamlit chat interface.
- `lean-api-server-flask.py` OpenAI API compatible proxy server. Can be plugged into any application that takes a OpenAI API model with custom base URL.
Can either use the API keys set in the environment variables, or take an API key token in the request,
which is then passed to the corresponding LLM.
Has been tested to work with [OpenWebUI](https://openwebui.com/), a fully featured chat interface, 
and [Continue](https://www.continue.dev/) and [Cline](https://cline.bot/), two VS Code plugin coding assistants.

### Example Set Up with OpenWebUI

- After the Installation steps above, the following command will launch the API server at `http://localhost:8000/v1`:
```
poetry run python lean-api-server-flask.py
```

- Install [OpenWebUI](https://openwebui.com/). If you go with the docker option, you will need to install docker first.
  Since our proxy server exposes an OpenAI compatible API, you can use 
the [docker command for installing OpenWebUI with OpenAI API](https://github.com/open-webui/open-webui?tab=readme-ov-file#installation-for-openai-api-usage-only)
adding the command line option `--add-host host.docker.internal:host-gateway -e OPENAI_API_BASE_URL=http://host.docker.internal:8000/v1`
- Access OpenWebUI at [http://localhost:3000/](http://localhost:3000/).

### Example Set Up with Continue.dev

- After the API server is running, install Continue as a VS Code extension.  
Follow the instructions [here](https://docs.continue.dev/customize/model-providers/openai)
to set up an OpenAI-compatible model by specifying an `apiBase` url.
Set the model name to be the key name of your chosen model in the models dict in `leantool.py`, e.g. "sonnet".
For the `apiKey` field you may provide your API key for the chosen model.

### Example Set Up with Cline

- Install the Cline VS Code extension. Set the model type to be OpenAI-compatible, and provide the base url.
Set the model name for your chosen model, e.g. "sonnet", and your API key.

