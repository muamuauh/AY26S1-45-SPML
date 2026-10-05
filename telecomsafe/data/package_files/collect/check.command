#!/bin/bash
# macOS: double-click to check ./submission and pack it (first time: right-click → Open, see README.md).
cd "$(dirname "$0")" || exit 1
if source tools/uv.sh; then
  uv run --no-project --python 3.12 --with pillow python tools/check.py
fi
echo
read -r -p "Press Enter to close."
