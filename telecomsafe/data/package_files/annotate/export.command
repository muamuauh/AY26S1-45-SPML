#!/bin/bash
# macOS: double-click to export deliverable/annotations.json.
cd "$(dirname "$0")" || exit 1
if source tools/env.sh && "$VENV/bin/python" tools/ls_tool.py export; then
  read -r -p "Press Enter to close."
  exit 0
fi
echo
echo "Something went wrong - see README.md, section FAQ."
read -r -p "Press Enter to close."
exit 1
