import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
PACKAGES = API_ROOT.parent
for entry in (API_ROOT, *PACKAGES.glob("*")):
    if entry.is_dir() and str(entry) not in sys.path:
        sys.path.insert(0, str(entry))
