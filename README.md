# LeanTool

This is a simple utility to arm LLMs with a "Code Interpreter" for Lean. Uses [LiteLLM](https://github.com/BerriAI/litellm) so you can plug in any compatible LLM, from OpenAI and Anthropic APIs to local LLMs hosted via ollama or vLLM.

Uses [Pantograph](https://github.com/lenianiva/PyPantograph/) to extract goal states from `sorry`s.

Currently used by [FormalizeWithTest](https://github.com/GasStationManager/FormalizeWithTest) autoformalization project.

## Installation

- Install Lean
- Install `poetry`
- Clone the repository
- Install [Pantograph](https://github.com/lenianiva/PyPantograph/) by following its instructions. Create the wheel file. 
- Modify `pyproject.toml` in the LeanTool directory, to ensure the `pantograph` entry points to the correct path and file name to the `.whl` file.
- `poetry install`
- Install Mathlib as needed

## Files

- `leantool.py` Python library
- `cli_chat.py` simple command line chat interface
- `app.py` Streamlit chat interface
