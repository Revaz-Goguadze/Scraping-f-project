"""Main entry point for the E-Commerce Price Monitoring System."""

import sys
from pathlib import Path

# Add src to path for imports to ensure modules are found
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.cli.interface import cli

if __name__ == '__main__':
    cli()