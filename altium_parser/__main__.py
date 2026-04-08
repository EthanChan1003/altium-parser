"""Allow running with ``python -m altium_parser``."""
import sys
from .cli import main

sys.exit(main())
