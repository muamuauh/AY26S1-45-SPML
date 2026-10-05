#!/bin/bash
# Makes sure uv and the Python environment with Label Studio exist, and sets VENV. Sourced by the .command files.
# The environment lives outside the package, so the package folder stays small and can be moved.
export VENV="$HOME/.telecomeval/venv-ls1.23.1"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "[setup] Installing uv, a small Python installer ..."
  curl -LsSf https://astral.sh/uv/install.sh | sh || return 1
  export PATH="$HOME/.local/bin:$PATH"
fi
command -v uv >/dev/null 2>&1 || { echo "[setup] uv could not be installed. See README.md, FAQ."; return 1; }
if [ ! -x "$VENV/bin/label-studio" ]; then
  echo "[setup] First run: installing Python 3.12 and Label Studio into $VENV"
  echo "[setup] This takes 5-10 minutes ..."
  uv venv "$VENV" --python 3.12 --allow-existing || return 1
  uv pip install --python "$VENV/bin/python" "label-studio==1.23.1" || return 1
fi
return 0
