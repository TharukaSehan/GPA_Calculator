# Repository Overview

This workspace currently contains a single Python script, `help.py`, which is intended to be the starting point for a GPA calculator project. At the moment the file merely attempts to print a message and is syntactically incorrect (`print hello world` without quotes).

Because this is a minimal skeleton project, most of the instructions here are about the small scale and how to expand it rather than about a complex architecture.

## Big Picture

- **Purpose**: Build a GPA calculator. The repository currently has no defined package structure or modules.
- **Structure**: Only `help.py` exists. In the future, expect to add modules under this root folder (e.g. `calculator.py`, `models.py`, `tests/`).
- **Data flow**: None yet. Expect to read course/grade input, compute GPA, output results.
- **Dependencies**: None outside the standard Python library.

## Running & Development

- Use a Python 3 interpreter on Windows (or any OS).
- Run `python help.py` from the workspace root to execute the script.
- There is no build process, packaging, or tests currently.
- If you add new files, keep them simple and import from `help.py` or a new `main.py` entry point.

## Project Conventions

- Use snake_case for filenames and functions, as is typical for Python projects.
- Keep code self‑contained in the root folder until a need for packages arises.
- When adding more substantial logic, split into modules and create a `tests/` directory for unit tests.

## AI agent guidance

- **Start by fixing syntax**: `help.py` should use `print("hello world")` or similar. The agent can propose the fix when asked about running the project.
- **General advice**: There are no hidden workflows; anything you write runs with plain `python`.
- **Expanding the application**: If tasked with adding GPA calculation functionality, create new modules (e.g. `gpa.py`) and import them. Write clear docstrings and add tests if requested.
- **No external integration**: No database, network, or CLI framework is currently used.

## Typical tasks you might encounter

1. **Implement GPA logic** in a new module; add command‑line input handling in `help.py` or `main.py`.
2. **Add tests** under a `tests` directory and run them with `python -m unittest`.
3. **Correct or enhance the existing script** as described above.

> **Note:** If new files or folders are introduced, update these instructions accordingly to keep an AI agent aware of the evolving project structure.


---

Please review these instructions and let me know if there are other patterns or details you’d like to capture. Adjustments can be made as the project grows or if there’s additional context I’ve missed.