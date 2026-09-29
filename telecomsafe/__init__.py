"""TelecomSafe — phase 1 baseline: public-data detector, rule-based risk judgement, demo."""

import sys

__version__ = "0.1.0"

# Windows consoles and redirected output may use a legacy code page (e.g. GBK); never crash on ✓ / ≈.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure") and (_stream.encoding or "").lower() not in ("utf-8", "utf8"):
        _stream.reconfigure(errors="replace")
