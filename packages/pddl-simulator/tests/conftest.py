"""Make sibling test-helper modules (e.g. `_sailing_helpers`) importable."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))
