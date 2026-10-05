#!/bin/bash
# Makes sure uv (a small Python installer) is available. Sourced by check.command.
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "[setup] Installing uv, a small Python installer ..."
  curl -LsSf https://astral.sh/uv/install.sh | sh || return 1
  export PATH="$HOME/.local/bin:$PATH"
fi
command -v uv >/dev/null 2>&1 || { echo "[setup] uv could not be installed. See README.md, FAQ."; return 1; }
return 0
