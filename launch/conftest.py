import sys
from pathlib import Path

_LAUNCH_ROOT = Path(__file__).resolve().parent
if str(_LAUNCH_ROOT) not in sys.path:
    sys.path.insert(0, str(_LAUNCH_ROOT))
