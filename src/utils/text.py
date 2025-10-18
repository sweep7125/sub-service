"""Text processing utilities."""

import codecs
import logging

logger = logging.getLogger(__name__)


def decode_unicode_escapes(text: str) -> str:
    """Decode unicode escape sequences in text.

    Handles \\u and \\U escape sequences commonly found in configuration files.

    Args:
        text: Input text potentially containing unicode escapes

    Returns:
        Decoded text or original text if decoding fails

    Example:
        >>> decode_unicode_escapes("\\u0420\\u0443\\u0441\\u0441\\u043a\\u0438\\u0439")
        'Русский'
    """
    if "\\u" not in text and "\\U" not in text:
        return text

    try:
        return codecs.decode(text, "unicode_escape")
    except (UnicodeDecodeError, ValueError) as e:
        logger.warning(f"Failed to decode unicode escapes in '{text[:50]}...': {e}")
        return text
