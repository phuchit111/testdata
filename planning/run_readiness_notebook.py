"""Execute this project's plain-Python readiness notebook without Jupyter.

This runner executes the code cells in order and saves their stream outputs.
It does not emulate IPython magics, rich displays, widgets, or a Jupyter kernel.
"""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import json
import os
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/00_workflow_readiness.ipynb"
sys.stdout.reconfigure(encoding="utf-8")
notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
assert notebook["nbformat"] == 4
scope = {"__name__": "__main__"}
code_cells = 0
previous_cwd = Path.cwd()
try:
    os.chdir(ROOT)
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        code_cells += 1
        stream = StringIO()
        cell["execution_count"] = code_cells
        cell["outputs"] = []
        try:
            with redirect_stdout(stream):
                exec(compile("".join(cell["source"]), f"{NOTEBOOK.name}:cell-{code_cells}", "exec"), scope)
        except Exception as exc:
            cell["outputs"].append({"output_type": "error", "ename": type(exc).__name__, "evalue": str(exc), "traceback": traceback.format_exc().splitlines()})
            raise
        finally:
            if stream.getvalue():
                cell["outputs"].insert(0, {"output_type": "stream", "name": "stdout", "text": stream.getvalue().splitlines(keepends=True)})
finally:
    os.chdir(previous_cwd)
    notebook["metadata"]["execution_method"] = "Sequential plain Python code cells; no Jupyter kernel"
    NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

print(json.dumps({"executed_code_cells": code_cells, "notebook": str(NOTEBOOK), "source_unchanged": True, "execution_method": "plain_python"}, ensure_ascii=False))
