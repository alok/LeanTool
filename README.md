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
- Flexible usage: as python library, as command-line chat interface, or as OpenAI-compatible API server

## Installation

- Install Lean
- Install `poetry`
- Clone the repository
- Install [Pantograph](https://github.com/lenianiva/PyPantograph/) by following its instructions. Create the wheel file. 
- Modify `pyproject.toml` in the LeanTool directory, to ensure the `pantograph` entry points to the correct path and file name to the `.whl` file.
- `poetry install`
- Install Mathlib as needed
- Set up your LLM model to connect via `LiteLLM`. E.g. for OpenAI, just set the environmental variable `OPENAI_API_KEY`. 
  For Anthropic, `ANTHROPIC_API_KEY`. For local models served by ollama, start by installing ollama. 
  See [Relevant LiteLLM Docs](https://docs.litellm.ai/docs/providers) for more detailed instructions. 
  The `models` dict in `leantool.py` has some preset models; it has the format short name -> LiteLLM model name. Modify it to have an entry for your model 
  if you have something different.

## Files

- `leantool.py` Python library. Simply import the file and call `interactive_lean_check` to invoke the feedback loop.
Currently used by [FormalizeWithTest](https://github.com/GasStationManager/FormalizeWithTest) autoformalization project.
- `cli_chat.py` command line chat interface.
- `app.py` Streamlit chat interface.
- `lean-api-server-flask.py` OpenAI API compatible proxy server. Can be plugged into any application that takes a OpenAI API model with custom base URL. 
Has been tested to work with [OpenWebUI](https://openwebui.com/), a fully featured chat interface, 
and [Continue](https://www.continue.dev/), a VS Code plugin coding assistant.

