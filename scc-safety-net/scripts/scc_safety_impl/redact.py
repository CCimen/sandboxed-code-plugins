"""Secret redaction and output sanitization for SCC Safety Net.

This module provides utilities to:
1. Redact known secret patterns from error messages
2. Truncate output to prevent log flooding
3. Combine both for safe error output

The redaction is applied BEFORE truncation to ensure secrets
are never partially exposed through truncation boundaries.

Usage:
    from .redact import safe_output

    # In error handling:
    print(safe_output(reason), file=sys.stderr)
"""

from __future__ import annotations

import re

# ─────────────────────────────────────────────────────────────────────────────
# Secret Patterns (High-Value Only)
# ─────────────────────────────────────────────────────────────────────────────

# Patterns are tuples of (regex_pattern, replacement)
# Only include high-value patterns to avoid over-redaction
SECRET_PATTERNS: list[tuple[str, str]] = [
    # Generic secret keywords with values
    (
        r"(?i)(api[_-]?key|token|secret|password|passwd|pwd)[=:]\s*['\"]?[\w\-]{8,}['\"]?",
        "[REDACTED]",
    ),
    # AWS credentials
    (
        r"(?i)aws[_-]?(access[_-]?key[_-]?id|secret[_-]?access[_-]?key)[=:]\s*[\w/+=]{16,}",
        "[AWS_KEY]",
    ),
    # GitHub personal access token (classic) - ghp_xxxx
    (r"ghp_[a-zA-Z0-9]{36}", "[GITHUB_TOKEN]"),
    # GitHub OAuth token - gho_xxxx
    (r"gho_[a-zA-Z0-9]{36}", "[GITHUB_TOKEN]"),
    # GitHub fine-grained PAT - github_pat_xxxx
    (r"github_pat_[a-zA-Z0-9_]{22,}", "[GITHUB_PAT]"),
    # GitHub App installation token - ghs_xxxx
    (r"ghs_[a-zA-Z0-9]{36}", "[GITHUB_TOKEN]"),
    # URL credentials (user:pass@host)
    (r"://[^:]+:[^@]+@", "://[CREDENTIALS]@"),
]

# Pre-compile patterns for efficiency
_COMPILED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pattern), replacement) for pattern, replacement in SECRET_PATTERNS
]

# ─────────────────────────────────────────────────────────────────────────────
# Default Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_MAX_LENGTH = 200


# ─────────────────────────────────────────────────────────────────────────────
# Redaction Functions
# ─────────────────────────────────────────────────────────────────────────────


def redact_secrets(text: str) -> str:
    """Mask known secret patterns in text.

    Applies all SECRET_PATTERNS to the input text, replacing
    matches with their corresponding replacement strings.

    Args:
        text: Input text that may contain secrets

    Returns:
        Text with secrets redacted
    """
    for pattern, replacement in _COMPILED_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def truncate(text: str, max_len: int = DEFAULT_MAX_LENGTH) -> str:
    """Truncate text to maximum length with ellipsis.

    Args:
        text: Input text to truncate
        max_len: Maximum length (default 200)

    Returns:
        Truncated text with '...' suffix if exceeded
    """
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def safe_output(text: str, max_len: int = DEFAULT_MAX_LENGTH) -> str:
    """Redact secrets and truncate for safe output.

    IMPORTANT: Redaction is applied BEFORE truncation to ensure
    secrets are never partially exposed through truncation boundaries.

    Args:
        text: Input text to sanitize
        max_len: Maximum output length (default 200)

    Returns:
        Sanitized text safe for logging/display
    """
    # Order matters: redact THEN truncate
    text = redact_secrets(text)
    text = truncate(text, max_len)
    return text
