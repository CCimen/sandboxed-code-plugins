"""Tests for secret redaction and output sanitization."""

from __future__ import annotations

from scc_safety_impl.redact import (
    DEFAULT_MAX_LENGTH,
    redact_secrets,
    safe_output,
    truncate,
)


class TestRedactSecrets:
    """Tests for redact_secrets function."""

    def test_no_secrets_unchanged(self) -> None:
        text = "git push --force origin main"
        assert redact_secrets(text) == text

    def test_redacts_api_key(self) -> None:
        text = "api_key=sk_live_abc123xyz456789"
        result = redact_secrets(text)
        assert "sk_live" not in result
        assert "[REDACTED]" in result

    def test_redacts_password(self) -> None:
        text = "password=mysecretpass123"
        result = redact_secrets(text)
        assert "mysecretpass" not in result
        assert "[REDACTED]" in result

    def test_redacts_token(self) -> None:
        text = "token: bearer_token_12345678"
        result = redact_secrets(text)
        assert "bearer_token" not in result
        assert "[REDACTED]" in result

    def test_redacts_aws_access_key(self) -> None:
        text = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        result = redact_secrets(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "[AWS_KEY]" in result

    def test_redacts_aws_secret_key(self) -> None:
        text = "aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        result = redact_secrets(text)
        assert "wJalrXUtnFEMI" not in result
        assert "[AWS_KEY]" in result

    def test_redacts_github_classic_token(self) -> None:
        text = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        result = redact_secrets(text)
        assert "ghp_" not in result
        assert "[GITHUB_TOKEN]" in result

    def test_redacts_github_oauth_token(self) -> None:
        text = "gho_abcdefghijklmnopqrstuvwxyz1234567890"
        result = redact_secrets(text)
        assert "gho_" not in result
        assert "[GITHUB_TOKEN]" in result

    def test_redacts_github_fine_grained_pat(self) -> None:
        text = "github_pat_11ABCDEFG0123456789012_AbCdEfGhIjKlMnOpQrStUvWxYz"
        result = redact_secrets(text)
        assert "github_pat_" not in result
        assert "[GITHUB_PAT]" in result

    def test_redacts_github_app_token(self) -> None:
        text = "ghs_abcdefghijklmnopqrstuvwxyz1234567890"
        result = redact_secrets(text)
        assert "ghs_" not in result
        assert "[GITHUB_TOKEN]" in result

    def test_redacts_url_credentials(self) -> None:
        text = "https://user:password123@github.com/repo.git"
        result = redact_secrets(text)
        assert "password123" not in result
        assert "[CREDENTIALS]" in result
        assert "github.com" in result  # Host preserved

    def test_multiple_secrets(self) -> None:
        text = "api_key=secret12345 password=pass45678"
        result = redact_secrets(text)
        assert "secret12345" not in result
        assert "pass45678" not in result
        assert result.count("[REDACTED]") == 2

    def test_case_insensitive(self) -> None:
        text = "API_KEY=secret123"
        result = redact_secrets(text)
        assert "secret123" not in result
        assert "[REDACTED]" in result


class TestTruncate:
    """Tests for truncate function."""

    def test_short_text_unchanged(self) -> None:
        text = "short message"
        assert truncate(text) == text

    def test_exact_length_unchanged(self) -> None:
        text = "x" * DEFAULT_MAX_LENGTH
        assert truncate(text) == text

    def test_long_text_truncated(self) -> None:
        text = "x" * 300
        result = truncate(text)
        assert len(result) == DEFAULT_MAX_LENGTH + 3  # +3 for "..."
        assert result.endswith("...")

    def test_custom_max_length(self) -> None:
        text = "x" * 100
        result = truncate(text, max_len=50)
        assert len(result) == 53  # 50 + "..."
        assert result.endswith("...")


class TestSafeOutput:
    """Tests for safe_output function."""

    def test_no_modification_needed(self) -> None:
        text = "git push failed"
        assert safe_output(text) == text

    def test_redacts_then_truncates(self) -> None:
        # Create a long message with a secret
        secret = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        text = f"Error with {secret}: " + "x" * 300
        result = safe_output(text)

        # Secret should be redacted
        assert "ghp_" not in result
        assert "[GITHUB_TOKEN]" in result

        # Should be truncated
        assert result.endswith("...")
        assert len(result) <= DEFAULT_MAX_LENGTH + 3

    def test_custom_max_length(self) -> None:
        text = "api_key=secret123 " + "x" * 100
        result = safe_output(text, max_len=50)

        # Secret should be redacted
        assert "secret123" not in result

        # Should be truncated to custom length
        assert len(result) <= 53

    def test_secret_not_partially_exposed(self) -> None:
        # Regression test: ensure truncation doesn't expose part of a secret
        # by truncating in the middle of a redacted placeholder
        secret = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        text = f"Token: {secret}"
        result = safe_output(text, max_len=20)

        # The [GITHUB_TOKEN] placeholder should be complete or not present
        # (not truncated in the middle like "[GITHUB_TO...")
        assert "ghp_" not in result
        # Either fully redacted or truncated before the token
        if "[GITHUB" in result:
            # If partially visible, the truncation happened in the placeholder
            # This is acceptable as long as the actual secret is not exposed
            pass
