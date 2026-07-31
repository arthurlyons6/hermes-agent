"""
Tests for the Lyons Command Center response sanitizer.
Verifies that [PERSON_NAME] placeholders are correctly replaced with the authorized name.
"""

import pytest
from sanitize_response import (
    sanitize_person_name, 
    validate_sanitization, 
    contains_person_name_placeholder,
    PERSON_NAME_PATTERN
)


class TestPersonNameSanitization:
    """Test suite for PERSON_NAME placeholder sanitization."""
    
    def test_basic_placeholder_replacement(self):
        """Test that [PERSON_NAME] is replaced with authorized name."""
        original = "I'm [PERSON_NAME], your Chief of Staff."
        expected = "I'm Arthur Lyons, your Chief of Staff."
        result = sanitize_person_name(original, authorized_name="Arthur Lyons")
        assert result == expected
    
    def test_curly_brace_variations(self):
        """Test that {PERSON_NAME} and {{PERSON_NAME}} are handled."""
        test_cases = [
            ("The authority is {PERSON_NAME}, Founder.", "Arthur Lyons"),
            ("Hello {{PERSON_NAME}}, how may I assist?", "Arthur Lyons"),
        ]
        
        for original, name in test_cases:
            result = sanitize_person_name(original, authorized_name=name)
            # Verify the placeholder was replaced
            assert "{PERSON_NAME}" not in result
            assert "{{PERSON_NAME}}" not in result
            assert name in result
    
    def test_multiple_placeholders(self):
        """Test handling of multiple placeholders in one response."""
        original = "Multiple [PERSON_NAME] in one [PERSON_NAME] response."
        result = sanitize_person_name(original, authorized_name="Arthur Lyons")
        assert result.count("Arthur Lyons") == 2
        assert "[PERSON_NAME]" not in result
    
    def test_no_placeholder_unchanged(self):
        """Test that text without placeholders remains unchanged."""
        original = "No placeholder here, just normal text."
        result = sanitize_person_name(original, authorized_name="Arthur Lyons")
        assert result == original
    
    def test_generic_name_not_replaced(self):
        """Test that [NAME] is NOT replaced (too generic)."""
        original = "Template: Dear [NAME], please contact us."
        result = sanitize_person_name(original, authorized_name="Arthur Lyons")
        assert result == original  # [NAME] should remain unchanged
    
    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        test_cases = [
            "[person_name]",
            "[Person_Name]",
            "[PERSON_name]",
        ]
        
        for variant in test_cases:
            result = sanitize_person_name(variant, authorized_name="Arthur Lyons")
            assert result == "Arthur Lyons", f"Failed for variant: {variant}"
    
    def test_rejects_non_string_input(self):
        """Test that non-string input raises TypeError."""
        with pytest.raises(TypeError):
            sanitize_person_name(123, authorized_name="Arthur Lyons")
        
        with pytest.raises(TypeError):
            sanitize_person_name(None, authorized_name="Arthur Lyons")
    
    def test_rejects_missing_authorized_name(self):
        """Test that missing authorized_name raises ValueError."""
        with pytest.raises(ValueError):
            sanitize_person_name("Test text", authorized_name="")
    
    def test_empty_string(self):
        """Test handling of empty string."""
        result = sanitize_person_name("", authorized_name="Arthur Lyons")
        assert result == ""
    
    def test_validation_detects_placeholder(self):
        """Test validation function correctly identifies placeholders."""
        original = "I'm [PERSON_NAME] here."
        sanitized = sanitize_person_name(original, authorized_name="Arthur Lyons")
        validation = validate_sanitization(original, sanitized)
        
        assert validation["had_placeholder"] is True
        assert validation["placeholder_removed"] is True
        assert validation["sanitization_successful"] is True
    
    def test_validation_confirms_no_placeholder(self):
        """Test validation function confirms no placeholders in clean text."""
        original = "This text has no placeholders."
        sanitized = sanitize_person_name(original, authorized_name="Arthur Lyons")
        validation = validate_sanitization(original, sanitized)
        
        assert validation["had_placeholder"] is False
        assert validation["sanitization_successful"] is True
    
    def test_contains_person_name_placeholder_detection(self):
        """Test placeholder detection function."""
        assert contains_person_name_placeholder("I'm [PERSON_NAME] here.") is True
        assert contains_person_name_placeholder("No placeholder here.") is False
        assert contains_person_name_placeholder("{PERSON_NAME}") is True
        assert contains_person_name_placeholder("{{PERSON_NAME}}") is True
        assert contains_person_name_placeholder("[NAME]") is False  # Not PERSON_NAME


class TestPatternMatching:
    """Test the regex pattern used for matching."""
    
    def test_pattern_matches_various_formats(self):
        """Test that the pattern matches various placeholder formats."""
        test_strings = [
            "[PERSON_NAME]",
            "{PERSON_NAME}",
            "{{PERSON_NAME}}",
            "[person_name]",
            "[PERSON_name]",
        ]
        
        for test_str in test_strings:
            match = PERSON_NAME_PATTERN.search(test_str)
            assert match is not None, f"Pattern failed to match: {test_str}"
    
    def test_pattern_does_not_match_generic_name(self):
        """Test that the pattern doesn't match [NAME]."""
        test_strings = [
            "[NAME]",
            "[name]",
            "Dear [NAME] sir",
        ]
        
        for test_str in test_strings:
            match = PERSON_NAME_PATTERN.search(test_str)
            assert match is None, f"Pattern incorrectly matched: {test_str}"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_whitespace_preservation(self):
        """Test that whitespace is preserved around replacements."""
        original = "  [PERSON_NAME]  "
        result = sanitize_person_name(original, authorized_name="Arthur Lyons")
        assert result == "  Arthur Lyons  "
    
    def test_newlines_preserved(self):
        """Test that newlines are preserved."""
        original = "Line 1\n[PERSON_NAME]\nLine 3"
        result = sanitize_person_name(original, authorized_name="Arthur Lyons")
        assert result == "Line 1\nArthur Lyons\nLine 3"
    
    def test_unicode_content(self):
        """Test handling of unicode content."""
        original = "[PERSON_NAME] — 专家, éxperto"
        result = sanitize_person_name(original, authorized_name="Arthur Lyons")
        assert "Arthur Lyons" in result
        assert "专家" in result
        assert "éxperto" in result
    
    def test_long_text(self):
        """Test handling of longer text with placeholder."""
        long_text = "This is a long paragraph. " * 50 + "[PERSON_NAME] is here."
        result = sanitize_person_name(long_text, authorized_name="Arthur Lyons")
        assert result.endswith("Arthur Lyons is here.")
        assert "[PERSON_NAME]" not in result