"""Entry point for ``python -m al_dic_3d`` — delegates to the CLI."""

from __future__ import annotations

import sys

from al_dic_3d.cli import main

if __name__ == "__main__":
    sys.exit(main())
