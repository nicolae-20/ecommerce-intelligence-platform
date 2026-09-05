from pathlib import Path
import sys


_REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
_PYTHON_DIRECTORY = str(_REPOSITORY_ROOT / "python")

if _PYTHON_DIRECTORY not in sys.path:
    sys.path.insert(0, _PYTHON_DIRECTORY)
