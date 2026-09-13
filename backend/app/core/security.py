"""
Security utilities: safe filenames, path-traversal protection, API key handling.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import unicodedata
from pathlib import Path


_SAFE_PATTERN = re.compile(r"[^\w\-.]")
_DOTS = re.compile(r"\.{2,}")


def sanitize_filename(filename: str) -> str:
    """
    Produce a safe, path-traversal-proof filename.
    - Removes directory separators
    - Normalises unicode
    - Strips non-alphanumeric characters (except - and .)
    - Collapses multiple dots
    - Prepends a random prefix to prevent collisions
    """
    # Normalise unicode
    name = unicodedata.normalize("NFKD", filename)
    name = name.encode("ascii", "ignore").decode("ascii")

    # Strip directory separators first
    name = Path(name).name

    # Keep only safe chars
    name = _SAFE_PATTERN.sub("_", name)
    name = _DOTS.sub(".", name)
    name = name.strip("._")

    if not name:
        name = "upload"

    prefix = secrets.token_hex(8)
    return f"{prefix}_{name}"


def verify_storage_path(storage_root: Path, target: Path) -> Path:
    """Raise ValueError if target is outside storage_root (path traversal guard)."""
    try:
        target.resolve().relative_to(storage_root.resolve())
    except ValueError:
        raise ValueError(
            f"Path traversal detected: {target} is outside storage root {storage_root}"
        )
    return target


def generate_matter_token() -> str:
    """Generate a cryptographically secure matter access token."""
    return secrets.token_urlsafe(32)


def constant_time_compare(val1: str, val2: str) -> bool:
    """Timing-safe string comparison for API key validation."""
    return hmac.compare_digest(
        val1.encode("utf-8"),
        val2.encode("utf-8"),
    )


def hash_api_key(key: str) -> str:
    """One-way hash of an API key for storage/comparison."""
    return hashlib.sha256(key.encode()).hexdigest()
