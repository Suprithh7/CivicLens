"""
Language detection and translation service.
Provides automatic language detection and LLM-based translation capabilities.
"""

import logging
from typing import Optional
from langdetect import detect, LangDetectException

from app.services.llm_service import generate_completion, LLMError
from app.core.exceptions import CivicLensException

logger = logging.getLogger(__name__)


class LanguageError(CivicLensException):
    """Exception raised when language operations fail."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=500,
            details=details or {}
        )


# Supported languages with their ISO 639-1 codes and names
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "hi": "Hindi",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "ar": "Arabic",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "it": "Italian",
    "nl": "Dutch",
    "pl": "Polish",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",
    "el": "Greek",
    "he": "Hebrew",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "ur": "Urdu",
}

# Default language
DEFAULT_LANGUAGE = "en"


def detect_language(text: str) -> str:
    """
    Detect the language of the given text.
    
    Args:
        text: Text to detect language from
        
    Returns:
        ISO 639-1 language code (e.g., 'en', 'es', 'fr')
        
    Raises:
        LanguageError: If language detection fails
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for language detection, defaulting to English")
        return DEFAULT_LANGUAGE
    
    try:
        # Detect language using langdetect
        detected_code = detect(text)
        
        # Normalize language code
        detected_code = detected_code.lower()
        
        # Map 'zh' to 'zh-cn' for consistency
        if detected_code == "zh":
            detected_code = "zh-cn"
        
        logger.info(f"Detected language: {detected_code} from text: '{text[:50]}...'")
        
        return detected_code
        
    except LangDetectException as e:
        logger.warning(f"Language detection failed: {e}, defaulting to English")
        return DEFAULT_LANGUAGE
    except Exception as e:
        logger.error(f"Unexpected error in language detection: {e}")
        raise LanguageError(
            "Failed to detect language",
            details={"error": str(e)}
        )


def is_supported_language(language_code: str) -> bool:
    """
    Check if a language code is supported.
    
    Args:
        language_code: ISO 639-1 language code
        
    Returns:
        True if supported, False otherwise
    """
    return language_code.lower() in SUPPORTED_LANGUAGES


def get_language_name(language_code: str) -> str:
    """
    Get the human-readable name for a language code.
    
    Args:
        language_code: ISO 639-1 language code
        
    Returns:
        Language name (e.g., 'English', 'Spanish')
    """
    return SUPPORTED_LANGUAGES.get(language_code.lower(), "Unknown")


def normalize_language_code(language_code: Optional[str]) -> str:
    """
    Normalize and validate a language code.
    
    Args:
        language_code: Language code to normalize (can be None)
        
    Returns:
        Normalized language code, or default if invalid
    """
    if not language_code:
        return DEFAULT_LANGUAGE
    
    normalized = language_code.lower().strip()
    
    # Handle common variations
    if normalized in ["zh", "zh-hans"]:
        normalized = "zh-cn"
    elif normalized in ["zh-hant"]:
        normalized = "zh-tw"
    
    # Return normalized code if supported, otherwise default
    if is_supported_language(normalized):
        return normalized
    
    logger.warning(f"Unsupported language code: {language_code}, defaulting to {DEFAULT_LANGUAGE}")
    return DEFAULT_LANGUAGE


async def translate_text(
    text: str,
    target_language: str,
    source_language: str = "auto",
    context: Optional[str] = None
) -> str:
    """
    Translate text to the target language using LLM.
    
    Args:
        text: Text to translate
        target_language: Target language code (e.g., 'es', 'fr')
        source_language: Source language code (default: 'auto' for auto-detection)
        context: Optional context about the text (e.g., "government policy document")
        
    Returns:
        Translated text
        
    Raises:
        LanguageError: If translation fails
    """
    if not text or not text.strip():
        return text
    
    # Normalize language codes
    target_language = normalize_language_code(target_language)
    
    # If target is English and source is auto/English, no translation needed
    if target_language == DEFAULT_LANGUAGE and source_language in ["auto", DEFAULT_LANGUAGE]:
        return text
    
    target_lang_name = get_language_name(target_language)
    
    try:
        logger.info(f"Translating text to {target_lang_name} ({target_language})")
        
        # Build translation prompt
        context_note = f"\n\nContext: This text is from {context}." if context else ""
        
        system_message = f"""You are a professional translator specializing in government and policy documents.
Your task is to translate text accurately while maintaining:
- The original meaning and intent
- Appropriate formality and tone
- Technical accuracy for policy-related terms
- Cultural appropriateness

Translate ONLY the text provided. Do not add explanations, notes, or commentary."""

        user_prompt = f"""Translate the following text to {target_lang_name}:{context_note}

Text to translate:
{text}

Provide only the translation, nothing else."""

        translation = await generate_completion(
            prompt=user_prompt,
            system_message=system_message,
            temperature=0.3  # Lower temperature for more consistent translations
        )
        
        logger.info(f"Successfully translated text to {target_lang_name}")
        
        return translation.strip()
        
    except LLMError as e:
        logger.error(f"LLM error during translation: {e}")
        raise LanguageError(
            f"Failed to translate to {target_lang_name}",
            details={"error": str(e), "target_language": target_language}
        )
    except Exception as e:
        logger.error(f"Unexpected error during translation: {e}")
        raise LanguageError(
            "Translation failed",
            details={"error": str(e)}
        )


def get_multilingual_instruction(language_code: str) -> str:
    """
    Get instruction text for LLM to respond in a specific language.
    
    Args:
        language_code: Target language code
        
    Returns:
        Instruction text to include in prompts
    """
    language_code = normalize_language_code(language_code)
    
    if language_code == DEFAULT_LANGUAGE:
        return ""
    
    language_name = get_language_name(language_code)
    
    return f"\n\nIMPORTANT: Respond in {language_name}. Provide your entire response in {language_name}, maintaining clarity and accuracy."


def get_supported_languages_list() -> list[dict]:
    """
    Get a list of all supported languages.
    
    Returns:
        List of dictionaries with 'code' and 'name' keys
    """
    return [
        {"code": code, "name": name}
        for code, name in sorted(SUPPORTED_LANGUAGES.items(), key=lambda x: x[1])
    ]
