#!/usr/bin/env python3
"""
Lyons Command Center Response Sanitizer
Replaces [PERSON_NAME] placeholders with the authorized user's name in outgoing responses.
This ensures identity consistency while preserving historical context.
"""

import re
from pathlib import Path
from typing import Optional

# Pattern to match [PERSON_NAME] and variations (but NOT [NAME])
PERSON_NAME_PATTERN = re.compile(
    r'\[PERSON_NAME\]|\{PERSON_NAME\}|\{\{PERSON_NAME\}\}',
    flags=re.IGNORECASE
)

# Pattern to detect any unresolved identity placeholder (for validation)
IDENTITY_PLACEHOLDER_PATTERN = re.compile(
    r'\[PERSON_NAME\]|\{PERSON_NAME\}|\{\{PERSON_NAME\}\}',
    flags=re.IGNORECASE
)

# Pattern to detect Arthur Lyons in authorized identity files
ARTHUR_LYONS_PATTERN = re.compile(
    r"Arthur Lyons['’]? (?:is the|Chief of Staff|Founder|Principal|Final Authority)",
    re.IGNORECASE
)


def resolve_authorized_user_name(soul_path: Optional[Path] = None) -> Optional[str]:
    """
    Resolve the authorized user name only from an authorized SOUL/HOT_CONTEXT file.
    
    For the Lyons Command Center profile, this returns "Arthur Lyons" when the
    identity is verified in the authoritative context file.
    
    Args:
        soul_path: Optional path to SOUL.md or HOT_CONTEXT.md file
        
    Returns:
        "Arthur Lyons" if identity is verified, None otherwise
    """
    if soul_path is None:
        return None
    
    try:
        content = soul_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    
    if ARTHUR_LYONS_PATTERN.search(content):
        return "Arthur Lyons"
    
    return None


def sanitize_person_name(
    text: str,
    authorized_name: str,
) -> str:
    """
    Replace [PERSON_NAME] placeholders with the authorized user's name in response text.
    
    Args:
        text: The response text to sanitize
        authorized_name: The authorized user's name to substitute
        
    Returns:
        Sanitized text with placeholders replaced
        
    Raises:
        TypeError: If text is not a string
    """
    if not isinstance(text, str):
        raise TypeError("Response text must be a string")
    
    if not authorized_name:
        raise ValueError("authorized_name must be provided")
    
    # Replace all variations of the placeholder with the authorized name
    sanitized = PERSON_NAME_PATTERN.sub(authorized_name, text)
    
    return sanitized


def contains_person_name_placeholder(text: str) -> bool:
    """
    Check if text contains unresolved identity placeholders.
    
    Args:
        text: Text to check
        
    Returns:
        True if placeholder found, False otherwise
    """
    if not isinstance(text, str):
        return False
    
    return bool(IDENTITY_PLACEHOLDER_PATTERN.search(text))


def validate_sanitization(original: str, sanitized: str) -> dict:
    """
    Validate that sanitization was performed correctly.
    
    Args:
        original: Original response text
        sanitized: Sanitized response text
        
    Returns:
        Dict with validation results
    """
    had_placeholder = bool(IDENTITY_PLACEHOLDER_PATTERN.search(original))
    has_placeholder_after = bool(IDENTITY_PLACEHOLDER_PATTERN.search(sanitized))
    
    # Sanitization is successful when no placeholder remains
    sanitization_successful = not has_placeholder_after
    
    return {
        "original_length": len(original),
        "sanitized_length": len(sanitized),
        "had_placeholder": had_placeholder,
        "placeholder_removed": had_placeholder and not has_placeholder_after,
        "sanitization_successful": sanitization_successful
    }


if __name__ == "__main__":
    # Test the sanitizer
    test_cases = [
        ("I'm [PERSON_NAME], your Chief of Staff.", "Arthur Lyons"),
        ("The authority is {PERSON_NAME}, Founder.", "Arthur Lyons"),
        ("Hello {{PERSON_NAME}}, how may I assist?", "Arthur Lyons"),
        ("No placeholder here.", "Arthur Lyons"),
        ("Multiple [PERSON_NAME] in one [PERSON_NAME] response.", "Arthur Lyons"),
        ("Template: Dear [NAME],", "Arthur Lyons"),  # [NAME] should NOT be replaced
    ]
    
    print("=== RESPONSE SANITIZER TEST ===\n")
    
    for i, (test, name) in enumerate(test_cases, 1):
        result = sanitize_person_name(test, authorized_name=name)
        validation = validate_sanitization(test, result)
        
        print(f"Test {i}:")
        print(f"  Original:  {test}")
        print(f"  Sanitized: {result}")
        print(f"  Valid:     {validation['sanitization_successful']}")
        print()