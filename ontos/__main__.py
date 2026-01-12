"""
Entry point for `python -m ontos` invocation.

This module enables running Ontos as a Python module:
    python -m ontos map
    python -m ontos log -e feature -s "Session summary"
"""

from ontos.cli import main

if __name__ == "__main__":
    main()
