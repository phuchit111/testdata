"""Streamlit deployment entrypoint for the FruitBlend24 decision app.

The wrapper intentionally points at the versioned deliverable app so a
deployment rerun reloads the current QA-passed artifacts.
"""

from pathlib import Path
import runpy


APP_PATH = Path(__file__).resolve().parent / "deliverables" / "fruitblend24_run_001" / "app.py"

runpy.run_path(str(APP_PATH), run_name="__main__")
