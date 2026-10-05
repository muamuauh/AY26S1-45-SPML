#!/bin/bash
# macOS: double-click to start annotating (first time: right-click → Open, see README.md).
cd "$(dirname "$0")" || exit 1
if source tools/env.sh && "$VENV/bin/python" tools/ls_tool.py start; then exit 0; fi
echo
echo "Something went wrong - see README.md, section FAQ."
read -r -p "Press Enter to close."
exit 1
