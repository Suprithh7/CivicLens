"""
Additional tests for scenario-based policy simplification.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.simplification_service import (
    simplify_policy,
    SimplificationError
)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_scenario_based_explanation_student(mock_generate, mock_get_text, mock_db):
    """Test scenario-based explanation with student scenario."""
    # Mock responses
    mock_get_text.return_value = (
        "Student loan forgiveness program for low-income graduates...",
        "Student Loan Forgiveness Policy 2024"
    )
    mock_generate.return_value = """**Does This Apply to You?**
YES - This policy applies to students who graduated with federal student loans.

**What You Get**
Up to $10,000 in loan forgiveness if you earn less than $125,000/year.

**What You Need**
- Federal student loans (not private loans)
- Income below $125,000/year
- Graduated from an accredited institution

**Next Steps**
1. Visit studentaid.gov
2. Submit your application online
3. Provide income verification

**Important Dates**
Application deadline: December 31, 2024

**Required Documents**
- Tax returns from last year
- Student loan account numbers
- Proof of graduation"""

    # Simplify policy with student scenario
    result = await simplify_policy(
        policy_id="pol_test123",
        db=mock_db,
        explanation_type="scenario",
        scenario_type="student",
        scenario_details="22 years old, recent graduate with $30,000 in student loans"
    )

    # Verify
    assert result["policy_id"] == "pol_test123"
    assert result["explanation_type"] == "scenario"
    assert "student" in result["simplified_text"].lower() or "loan" in result["simplified_text"].lower()
    assert "timestamp" in result

    # Verify LLM was called with correct temperature
    mock_generate.assert_called_once()
    call_kwargs = mock_generate.call_args[1]
    assert call_kwargs["temperature"] == 0.5  # Default for scenario type


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_scenario_based_explanation_senior(mock_generate, mock_get_text, mock_db):
    """Test scenario-based explanation with senior citizen scenario."""
    # Mock responses
    mock_get_text.return_value = (
        "Medicare supplemental benefits for seniors...",
        "Medicare Advantage Policy"
    )
    mock_generate.return_value = """**Does This Apply to You?**
YES - This policy applies to seniors 65 and older.

**What You Get**
Additional coverage for prescription drugs, dental, and vision.

**What You Need**
- Age 65 or older
- Enrolled in Medicare Part A and B
- Live in the service area

**Next Steps**
1. Call 1-800-MEDICARE
2. Compare plans in your area
3. Enroll during open enrollment

**Important Dates**
Open enrollment: October 15 - December 7

**Required Documents**
- Medicare card
- Proof of residence
- Current medication list"""

    # Simplify policy with senior citizen scenario
    result = await simplify_policy(
        policy_id="pol_test456",
        db=mock_db,
        explanation_type="scenario",
        scenario_type="senior_citizen",
        scenario_details="68 years old, retired, on fixed income"
    )

    # Verify
    assert result["explanation_type"] == "scenario"
    assert "senior" in result["simplified_text"].lower() or "medicare" in result["simplified_text"].lower()


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
async def test_scenario_based_explanation_missing_type(mock_get_text, mock_db):
    """Test error when scenario_type is missing for scenario explanation type."""
    mock_get_text.return_value = ("Policy text...", "Policy Title")

    # Should raise error
    with pytest.raises(SimplificationError) as exc_info:
        await simplify_policy(
            policy_id="pol_test123",
            db=mock_db,
            explanation_type="scenario"
            # Missing scenario_type
        )

    assert "scenario_type is required" in str(exc_info.value)


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_scenario_based_explanation_with_details(mock_generate, mock_get_text, mock_db):
    """Test scenario-based explanation with additional scenario details."""
    mock_get_text.return_value = ("Policy text...", "Policy Title")
    mock_generate.return_value = "Scenario-specific explanation..."

    result = await simplify_policy(
        policy_id="pol_test123",
        db=mock_db,
        explanation_type="scenario",
        scenario_type="parent",
        scenario_details="Single parent with 2 children under 12, annual income $45,000"
    )

    # Verify scenario details were passed to prompt generation
    assert result["explanation_type"] == "scenario"
    mock_generate.assert_called_once()


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
@patch('app.services.simplification_service.detect_language')
async def test_scenario_based_explanation_multilingual(mock_detect_lang, mock_generate, mock_get_text, mock_db):
    """Test scenario-based explanation with multilingual support."""
    mock_get_text.return_value = ("Policy text...", "Policy Title")
    mock_generate.return_value = "Explicación basada en escenario..."
    mock_detect_lang.return_value = "es"

    result = await simplify_policy(
        policy_id="pol_test123",
        db=mock_db,
        explanation_type="scenario",
        scenario_type="unemployed",
        scenario_details="Buscando trabajo, desempleado desde hace 3 meses",
        language="es"
    )

    # Verify language was handled
    assert result["explanation_type"] == "scenario"
    assert result["response_language"] == "es"
