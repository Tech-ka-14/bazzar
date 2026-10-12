"""Backwards-compatible shim — the OpenAlgo client moved to
``backend.providers.openalgo`` in P3. Import from there in new code.
"""

from __future__ import annotations

from .providers.openalgo import (
    CredentialsNotConfigured,
    OpenAlgoClient,
    OpenAlgoProvider,
    load_dotenv,
    normalize_history,
)
from .providers.ratelimit import TokenBucket as _TokenBucket  # legacy alias

__all__ = [
    "CredentialsNotConfigured",
    "OpenAlgoClient",
    "OpenAlgoProvider",
    "load_dotenv",
    "normalize_history",
    "_TokenBucket",
]
