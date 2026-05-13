from pathlib import Path
import os
import runpy
import sys


DASHBOARD_DIR = Path(__file__).resolve().parent / "Dashboard"

os.chdir(DASHBOARD_DIR)
sys.path.insert(0, str(DASHBOARD_DIR))

runpy.run_path(str(DASHBOARD_DIR / "app.py"), run_name="__main__")
