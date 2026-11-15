"""Rebuild the offline packet from cached source records and central points weights."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for script in ("units/parse_catalog.py", "units/points.py", "units/update_forces.py",
               "units/generate_cards.py", "pilots/generate_cards.py", "web/build.py"):
    subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, check=True)
