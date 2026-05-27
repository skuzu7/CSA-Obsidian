# Contributing to automation-stealth

Thanks for your interest! Contributions of all sizes are welcome — bug reports, docs, tests, and features.

## Getting set up

```bash
git clone https://github.com/skuzu7/CSA-Obsidian
cd CSA-Obsidian
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -e ".[dev]"
```

## Before opening a PR

Run the checks locally — CI runs the same ones:

```bash
ruff check .          # lint
ruff format --check . # formatting
pytest -q             # tests
```

- Keep changes focused; one logical change per PR.
- Add or update tests for any behavior change.
- Match the existing code style in the file you touch.
- New exceptions go in `stealth_browser/errors.py` with structured attributes.
- New MCP tools use the `@_mcp_tool` decorator and a clear docstring (the LLM reads it).

## Reporting bugs

Open an issue with: what you expected, what happened, a minimal repro, and your OS / Python version.

## Responsible use

This is a stealth automation toolkit. Contributions must keep the project aligned with legitimate use cases (testing, QA, accessibility, personal automation, LLM agents). We won't merge features whose primary purpose is to defeat security controls or violate site Terms of Service.

## License

By contributing, you agree your contributions are licensed under the [MIT License](LICENSE).
