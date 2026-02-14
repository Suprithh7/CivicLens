"""
Tests for language detection and translation service.
"""

import pytest
from app.services.language_service import (
    detect_language,
    is_supported_language,
    get_language_name,
    normalize_language_code,
    get_multilingual_instruction,
    get_supported_languages_list
)


class TestLanguageDetection:
    """Test language detection functionality."""
    
    def test_detect_english(self):
        """Test detection of English text."""
        text = "What are the eligibility requirements for this program?"
        lang = detect_language(text)
        assert lang == "en"
    
    def test_detect_spanish(self):
        """Test detection of Spanish text."""
        text = "¿Cuáles son los requisitos de elegibilidad para este programa?"
        lang = detect_language(text)
        assert lang == "es"
    
    def test_detect_french(self):
        """Test detection of French text."""
        text = "Quels sont les critères d'éligibilité pour ce programme?"
        lang = detect_language(text)
        assert lang == "fr"
    
    def test_detect_hindi(self):
        """Test detection of Hindi text."""
        text = "इस कार्यक्रम के लिए पात्रता आवश्यकताएं क्या हैं?"
        lang = detect_language(text)
        assert lang == "hi"
    
    def test_detect_empty_text(self):
        """Test detection with empty text defaults to English."""
        lang = detect_language("")
        assert lang == "en"
    
    def test_detect_whitespace_only(self):
        """Test detection with whitespace only defaults to English."""
        lang = detect_language("   ")
        assert lang == "en"


class TestLanguageValidation:
    """Test language validation and normalization."""
    
    def test_is_supported_language_valid(self):
        """Test validation of supported language codes."""
        assert is_supported_language("en") is True
        assert is_supported_language("es") is True
        assert is_supported_language("fr") is True
        assert is_supported_language("hi") is True
    
    def test_is_supported_language_invalid(self):
        """Test validation of unsupported language codes."""
        assert is_supported_language("xx") is False
        assert is_supported_language("invalid") is False
    
    def test_is_supported_language_case_insensitive(self):
        """Test that language validation is case-insensitive."""
        assert is_supported_language("EN") is True
        assert is_supported_language("Es") is True
    
    def test_get_language_name(self):
        """Test getting language names from codes."""
        assert get_language_name("en") == "English"
        assert get_language_name("es") == "Spanish"
        assert get_language_name("fr") == "French"
        assert get_language_name("hi") == "Hindi"
    
    def test_get_language_name_unknown(self):
        """Test getting name for unknown language code."""
        assert get_language_name("xx") == "Unknown"
    
    def test_normalize_language_code_valid(self):
        """Test normalization of valid language codes."""
        assert normalize_language_code("en") == "en"
        assert normalize_language_code("EN") == "en"
        assert normalize_language_code("  es  ") == "es"
    
    def test_normalize_language_code_chinese_variants(self):
        """Test normalization of Chinese language variants."""
        assert normalize_language_code("zh") == "zh-cn"
        assert normalize_language_code("zh-hans") == "zh-cn"
        assert normalize_language_code("zh-hant") == "zh-tw"
    
    def test_normalize_language_code_invalid(self):
        """Test normalization of invalid codes defaults to English."""
        assert normalize_language_code("invalid") == "en"
        assert normalize_language_code("xx") == "en"
    
    def test_normalize_language_code_none(self):
        """Test normalization of None defaults to English."""
        assert normalize_language_code(None) == "en"


class TestMultilingualInstructions:
    """Test multilingual instruction generation."""
    
    def test_get_multilingual_instruction_english(self):
        """Test that English returns empty instruction."""
        instruction = get_multilingual_instruction("en")
        assert instruction == ""
    
    def test_get_multilingual_instruction_spanish(self):
        """Test Spanish instruction generation."""
        instruction = get_multilingual_instruction("es")
        assert "Spanish" in instruction
        assert "Respond in Spanish" in instruction
    
    def test_get_multilingual_instruction_french(self):
        """Test French instruction generation."""
        instruction = get_multilingual_instruction("fr")
        assert "French" in instruction
        assert "Respond in French" in instruction
    
    def test_get_multilingual_instruction_invalid(self):
        """Test invalid language code defaults to English (empty)."""
        instruction = get_multilingual_instruction("invalid")
        assert instruction == ""


class TestSupportedLanguages:
    """Test supported languages list."""
    
    def test_get_supported_languages_list(self):
        """Test getting list of supported languages."""
        languages = get_supported_languages_list()
        
        # Should be a list
        assert isinstance(languages, list)
        
        # Should have multiple languages
        assert len(languages) > 10
        
        # Each item should have code and name
        for lang in languages:
            assert "code" in lang
            assert "name" in lang
            assert isinstance(lang["code"], str)
            assert isinstance(lang["name"], str)
        
        # Should include common languages
        codes = [lang["code"] for lang in languages]
        assert "en" in codes
        assert "es" in codes
        assert "fr" in codes
        assert "hi" in codes
    
    def test_supported_languages_sorted(self):
        """Test that supported languages are sorted by name."""
        languages = get_supported_languages_list()
        names = [lang["name"] for lang in languages]
        
        # Should be sorted alphabetically
        assert names == sorted(names)
