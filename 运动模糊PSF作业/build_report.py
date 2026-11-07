"""Compatibility wrapper: build the report from its XeLaTeX source."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
script = root / "compile_report.ps1"
subprocess.run(["powershell.exe", "-NoProfile", "-File", str(script)], cwd=root, check=True)
