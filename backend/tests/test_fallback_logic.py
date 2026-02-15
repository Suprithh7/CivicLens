"""
Tests for AI uncertainty detection and fallback logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.simplification_service import (
    detect_uncertainty,
    generate_fallback_response,
    simplify_policy
)


def test_detect_uncertainty_high_confidence():
    """Test uncertainty detection with high confidence response."""
    response_text = """This policy provides clear benefits to eligible students.
    
    You can apply by visiting the website and submitting your application.
    The deadline is December 31, 2024."""
    
    policy_text = "A" * 500  # Sufficient length
    
    result = detect_uncertainty(response_text, policy_text)
    
    assert result["confidence"] == "high"
    assert not result["has_partial_answer"]


def test_detect_uncertainty_medium_confidence():
    """Test uncertainty detection with medium confidence indicators."""
    response_text = """Based on the available information, it appears this policy might apply to you.
    
    It seems that students could be eligible, but more details would help."""
    
    policy_text = "A" * 500
    
    result = detect_uncertainty(response_text, policy_text)
    
    assert result["confidence"] == "medium"


def test_detect_uncertainty_low_confidence():
    """Test uncertainty detection with low confidence indicators."""
    response_text = """I don't have enough information to determine if this applies to you.
    
    The policy text is incomplete and unclear about eligibility requirements."""
    
    policy_text = "A" * 500
    
    result = detect_uncertainty(response_text, policy_text)
    
    assert result["confidence"] == "low"


def test_detect_uncertainty_short_policy():
    """Test uncertainty detection with very short policy text."""
    response_text = "This is a response."
    policy_text = "Short text"  # Less than 200 characters
    
    result = detect_uncertainty(response_text, policy_text)
    
    assert result["confidence"] == "low"


def test_detect_uncertainty_missing_info():
    """Test detection of missing information indicators."""
    response_text = """I need more information about your income level to determine eligibility.
    
    The policy has missing information about application deadlines."""
    
    policy_text = "A" * 500
    
    result = detect_uncertainty(response_text, policy_text)
    
    assert result["has_partial_answer"]
    assert "suggestions" in result
    assert len(result["suggestions"]) > 0


def test_generate_fallback_insufficient_data():
    """Test fallback response generation for insufficient data."""
    response = generate_fallback_response(
        policy_id="pol_123",
        policy_title="Test Policy",
        explanation_type="scenario",
        reason="insufficient_data"
    )
    
    assert "Limited Information Available" in response
    assert "Test Policy" in response
    assert "Re-upload" in response


def test_generate_fallback_out_of_scope():
    """Test fallback response for out-of-scope scenarios."""
    response = generate_fallback_response(
        policy_id="pol_123",
        policy_title="Student Loan Policy",
        explanation_type="scenario",
        reason="out_of_scope"
    )
    
    assert "May Not Apply" in response
    assert "Student Loan Policy" in response
    assert "different scenario" in response


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_simplify_policy_with_short_text(mock_generate, mock_get_text):
    """Test simplify_policy with very short policy text (triggers fallback)."""
    # Mock very short policy text
    mock_get_text.return_value = ("Short", "Test Policy")
    mock_generate.return_value = "Some response"
    
    db = AsyncMock()
    
    result = await simplify_policy(
        policy_id="pol_123",
        db=db,
        explanation_type="explanation"
    )
    
    # Should use fallback response
    assert result["confidence_level"] == "low"
    assert result["is_partial_answer"] == False
    assert "Limited Information Available" in result["simplified_text"]
    assert result["missing_information"] is not None
    assert "Complete policy text" in result["missing_information"]


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_simplify_policy_with_uncertain_response(mock_generate, mock_get_text):
    """Test simplify_policy when LLM response indicates uncertainty."""
    mock_get_text.return_value = ("A" * 500, "Test Policy")
    mock_generate.return_value = """I don't have enough information to determine eligibility.
    
    Based on the available information, it appears this might apply, but I need more details."""
    
    db = AsyncMock()
    
    result = await simplify_policy(
        policy_id="pol_123",
        db=db,
        explanation_type="eligibility",
        user_situation="Student with part-time job"
    )
    
    # Should detect low/medium confidence
    assert result["confidence_level"] in ["low", "medium"]
    assert result["suggestions"] is not None


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_simplify_policy_high_confidence(mock_generate, mock_get_text):
    """Test simplify_policy with high confidence response."""
    mock_get_text.return_value = ("A" * 500, "Test Policy")
    mock_generate.return_value = """This policy clearly applies to full-time students.
    
    You can apply online at example.gov. The deadline is December 31, 2024."""
    
    db = AsyncMock()
    
    result = await simplify_policy(
        policy_id="pol_123",
        db=db,
        explanation_type="explanation"
    )
    
    # Should have high confidence
    assert result["confidence_level"] == "high"
    assert not result["is_partial_answer"]
