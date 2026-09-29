"""Load API keys from the repository's .env file into os.environ.

Existing environment variables win over .env, so a key exported in the shell is
never silently replaced. Empty values are ignored (the template ships them empty).
"""

from __future__ import annotations

import os

from telecomsafe.paths import ROOT


def load_env(path=ROOT / ".env") -> list[str]:
    """Returns the names that were set from the file."""
    if not path.exists():
        return []
    loaded = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = (s.strip() for s in line.split("=", 1))
        value = value.strip("'\"")
        if key.startswith("export "):
            key = key[len("export "):].strip()
        if value and key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded
