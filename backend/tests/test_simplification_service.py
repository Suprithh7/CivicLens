"""
Tests for policy simplification service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.simplification_service import (
    get_policy_text,
    simplify_policy,
    SimplificationError
)
from app.models.policy import Policy, PolicyStatus, PolicyChunk, PolicyProcessing, ProcessingStage, ProcessingStatus
from app.services.llm_service import LLMError


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_policy():
    """Create a sample policy object."""
    policy = MagicMock(spec=Policy)
    policy.id = 1
    policy.policy_id = "pol_test123"
    policy.title = "Test Healthcare Policy"
    policy.status = PolicyStatus.ANALYZED
    return policy


@pytest.fixture
def sample_chunks():
    """Create sample policy chunks."""
    chunks = []
    for i in range(3):
        chunk = MagicMock(spec=PolicyChunk)
        chunk.id = i + 1
        chunk.policy_id = 1
        chunk.chunk_index = i
        chunk.chunk_text = f"This is chunk {i} of the policy document. It contains important information about healthcare benefits."
        chunks.append(chunk)
    return chunks


@pytest.mark.asyncio
async def test_get_policy_text_with_chunks(mock_db, sample_policy, sample_chunks):
    """Test retrieving policy text from chunks."""
    # Mock database queries
    policy_result = MagicMock()
    policy_result.scalar_one_or_none.return_value = sample_policy
    
    chunks_result = MagicMock()
    chunks_result.scalars.return_value.all.return_value = sample_chunks
    
    mock_db.execute.side_effect = [policy_result, chunks_result]
    
    # Get policy text
    text, title = await get_policy_text("pol_test123", mock_db)
    
    # Verify
    assert title == "Test Healthcare Policy"
    assert "chunk 0" in text
    assert "chunk 1" in text
    assert "chunk 2" in text
    assert text.count("\n\n") == 2  # Chunks joined with double newlines


@pytest.mark.asyncio
async def test_get_policy_text_from_processing_record(mock_db, sample_policy):
    """Test retrieving policy text from processing record when chunks don't exist."""
    # Mock database queries
    policy_result = MagicMock()
    policy_result.scalar_one_or_none.return_value = sample_policy
    
    chunks_result = MagicMock()
    chunks_result.scalars.return_value.all.return_value = []  # No chunks
    
    processing = MagicMock(spec=PolicyProcessing)
    processing.result_data = {
        "extracted_text": "This is the full extracted text from the policy document."
    }
    
    processing_result = MagicMock()
    processing_result.scalar_one_or_none.return_value = processing
    
    mock_db.execute.side_effect = [policy_result, chunks_result, processing_result]
    
    # Get policy text
    text, title = await get_policy_text("pol_test123", mock_db)
    
    # Verify
    assert title == "Test Healthcare Policy"
    assert text == "This is the full extracted text from the policy document."


@pytest.mark.asyncio
async def test_get_policy_text_policy_not_found(mock_db):
    """Test error when policy doesn't exist."""
    # Mock database query
    policy_result = MagicMock()
    policy_result.scalar_one_or_none.return_value = None
    
    mock_db.execute.return_value = policy_result
    
    # Should raise error
    with pytest.raises(SimplificationError) as exc_info:
        await get_policy_text("pol_nonexistent", mock_db)
    
    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_policy_text_no_text_available(mock_db, sample_policy):
    """Test error when no text is available."""
    # Mock database queries
    policy_result = MagicMock()
    policy_result.scalar_one_or_none.return_value = sample_policy
    
    chunks_result = MagicMock()
    chunks_result.scalars.return_value.all.return_value = []  # No chunks
    
    processing_result = MagicMock()
    processing_result.scalar_one_or_none.return_value = None  # No processing record
    
    mock_db.execute.side_effect = [policy_result, chunks_result, processing_result]
    
    # Should raise error
    with pytest.raises(SimplificationError) as exc_info:
        await get_policy_text("pol_test123", mock_db)
    
    assert "no text available" in str(exc_info.value).lower()


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_simplify_policy_explanation_type(mock_generate, mock_get_text, mock_db):
    """Test simplifying policy with explanation type."""
    # Mock responses
    mock_get_text.return_value = (
        "Policy text about healthcare benefits...",
        "Healthcare Policy 2024"
    )
    mock_generate.return_value = "This policy helps families get affordable healthcare..."
    
    # Simplify policy
    result = await simplify_policy(
        policy_id="pol_test123",
        db=mock_db,
        explanation_type="explanation"
    )
    
    # Verify
    assert result["policy_id"] == "pol_test123"
    assert result["policy_title"] == "Healthcare Policy 2024"
    assert result["explanation_type"] == "explanation"
    assert "affordable healthcare" in result["simplified_text"]
    assert "timestamp" in result
    
    # Verify LLM was called with correct temperature
    mock_generate.assert_called_once()
    call_kwargs = mock_generate.call_args[1]
    assert call_kwargs["temperature"] == 0.7  # Default for explanation type


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_simplify_policy_eligibility_type(mock_generate, mock_get_text, mock_db):
    """Test simplifying policy with eligibility type."""
    # Mock responses
    mock_get_text.return_value = (
        "Eligibility: Income below $50,000...",
        "Housing Assistance Policy"
    )
    mock_generate.return_value = "Yes, you are likely eligible because..."
    
    # Simplify policy
    result = await simplify_policy(
        policy_id="pol_test123",
        db=mock_db,
        explanation_type="eligibility",
        user_situation="I make $40,000 per year"
    )
    
    # Verify
    assert result["explanation_type"] == "eligibility"
    assert "eligible" in result["simplified_text"]
    
    # Verify LLM was called with lower temperature for factual response
    mock_generate.assert_called_once()
    call_kwargs = mock_generate.call_args[1]
    assert call_kwargs["temperature"] == 0.3


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
async def test_simplify_policy_eligibility_missing_situation(mock_get_text, mock_db):
    """Test error when user_situation is missing for eligibility type."""
    mock_get_text.return_value = ("Policy text...", "Policy Title")
    
    # Should raise error
    with pytest.raises(SimplificationError) as exc_info:
        await simplify_policy(
            policy_id="pol_test123",
            db=mock_db,
            explanation_type="eligibility"
            # Missing user_situation
        )
    
    assert "user_situation is required" in str(exc_info.value)


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_simplify_policy_key_points_type(mock_generate, mock_get_text, mock_db):
    """Test simplifying policy with key_points type."""
    mock_get_text.return_value = ("Policy text...", "Policy Title")
    mock_generate.return_value = "• Point 1\n• Point 2\n• Point 3"
    
    result = await simplify_policy(
        policy_id="pol_test123",
        db=mock_db,
        explanation_type="key_points",
        max_points=3
    )
    
    assert result["explanation_type"] == "key_points"
    assert "Point 1" in result["simplified_text"]


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
async def test_simplify_policy_invalid_type(mock_get_text, mock_db):
    """Test error with invalid explanation type."""
    mock_get_text.return_value = ("Policy text...", "Policy Title")
    
    with pytest.raises(SimplificationError) as exc_info:
        await simplify_policy(
            policy_id="pol_test123",
            db=mock_db,
            explanation_type="invalid_type"
        )
    
    assert "invalid explanation type" in str(exc_info.value).lower()


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_simplify_policy_llm_error(mock_generate, mock_get_text, mock_db):
    """Test handling of LLM errors."""
    mock_get_text.return_value = ("Policy text...", "Policy Title")
    mock_generate.side_effect = LLMError("API rate limit exceeded")
    
    with pytest.raises(SimplificationError) as exc_info:
        await simplify_policy(
            policy_id="pol_test123",
            db=mock_db,
            explanation_type="explanation"
        )
    
    assert "failed to generate" in str(exc_info.value).lower()
