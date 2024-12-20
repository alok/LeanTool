# LeanTool

This is a simple utility to arm LLMs with a "Code Interpreter" for Lean. Uses [LiteLLM](https://github.com/BerriAI/litellm) so you can plug in any compatible LLM, from OpenAI and Anthropic APIs to local LLMs hosted via ollama or vLLM.

Currently used by [FormalizeWithTest](https://github.com/GasStationManager/FormalizeWithTest) autoformalization project.

## Features

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

## Files

- `leantool.py` Python library.
- `cli_chat.py` command line chat interface
- `app.py` Streamlit chat interface
- `lean-api-server-flask.py` OpenAI API compatible proxy server

