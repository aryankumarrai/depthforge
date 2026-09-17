"""Convenience launcher for running DepthForge directly from the repository root."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from depthforge.cli import main

if __name__ == "__main__":
    main()
