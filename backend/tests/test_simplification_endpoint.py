"""
Integration tests for policy simplification API endpoint.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from app.main import app


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_explain_policy_success(mock_generate, mock_get_text, client):
    """Test successful policy simplification."""
    # Mock responses
    mock_get_text.return_value = (
        "This policy provides healthcare subsidies for low-income families...",
        "Healthcare Subsidy Program 2024"
    )
    mock_generate.return_value = (
        "This program helps families with low income get affordable healthcare. "
        "If your family makes less than $50,000 per year, you can get help paying for health insurance."
    )
    
    # Make request
    response = await client.post(
        "/api/v1/simplification/explain",
        json={
            "policy_id": "pol_test123",
            "explanation_type": "explanation"
        }
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["policy_id"] == "pol_test123"
    assert data["policy_title"] == "Healthcare Subsidy Program 2024"
    assert data["explanation_type"] == "explanation"
    assert "affordable healthcare" in data["simplified_text"]
    assert "model_used" in data
    assert "timestamp" in data


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_explain_policy_eligibility_type(mock_generate, mock_get_text, client):
    """Test eligibility check explanation type."""
    mock_get_text.return_value = (
        "Eligibility: Annual income below $50,000...",
        "Housing Assistance Policy"
    )
    mock_generate.return_value = "Yes, you are likely eligible because your income is below the threshold."
    
    response = await client.post(
        "/api/v1/simplification/explain",
        json={
            "policy_id": "pol_test123",
            "explanation_type": "eligibility",
            "user_situation": "I make $40,000 per year with two children"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["explanation_type"] == "eligibility"
    assert "eligible" in data["simplified_text"]


@pytest.mark.asyncio
async def test_explain_policy_eligibility_missing_situation(client):
    """Test validation error when user_situation is missing for eligibility type."""
    response = await client.post(
        "/api/v1/simplification/explain",
        json={
            "policy_id": "pol_test123",
            "explanation_type": "eligibility"
            # Missing user_situation
        }
    )
    
    assert response.status_code == 422
    data = response.json()
    assert "user_situation" in data["detail"]["message"].lower()


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_explain_policy_key_points_type(mock_generate, mock_get_text, client):
    """Test key points explanation type."""
    mock_get_text.return_value = ("Policy text...", "Policy Title")
    mock_generate.return_value = "• You can get free healthcare\n• Income must be below $50,000\n• Apply online"
    
    response = await client.post(
        "/api/v1/simplification/explain",
        json={
            "policy_id": "pol_test123",
            "explanation_type": "key_points",
            "max_points": 3
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["explanation_type"] == "key_points"
    assert "•" in data["simplified_text"]


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_explain_policy_benefits_type(mock_generate, mock_get_text, client):
    """Test benefits summary explanation type."""
    mock_get_text.return_value = ("Policy text...", "Policy Title")
    mock_generate.return_value = "You get free health insurance and dental coverage."
    
    response = await client.post(
        "/api/v1/simplification/explain",
        json={
            "policy_id": "pol_test123",
            "explanation_type": "benefits"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["explanation_type"] == "benefits"


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_explain_policy_application_type(mock_generate, mock_get_text, client):
    """Test application process explanation type."""
    mock_get_text.return_value = ("Policy text...", "Policy Title")
    mock_generate.return_value = "Step 1: Visit the website\nStep 2: Fill out the form\nStep 3: Submit documents"
    
    response = await client.post(
        "/api/v1/simplification/explain",
        json={
            "policy_id": "pol_test123",
            "explanation_type": "application"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["explanation_type"] == "application"
    assert "Step" in data["simplified_text"]


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
async def test_explain_policy_not_found(mock_get_text, client):
    """Test 404 error when policy doesn't exist."""
    from app.services.simplification_service import SimplificationError
    
    mock_get_text.side_effect = SimplificationError(
        "Policy not found: pol_nonexistent",
        details={"policy_id": "pol_nonexistent"}
    )
    
    response = await client.post(
        "/api/v1/simplification/explain",
        json={
            "policy_id": "pol_nonexistent",
            "explanation_type": "explanation"
        }
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]["message"].lower()


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
async def test_explain_policy_no_text_available(mock_get_text, client):
    """Test 400 error when policy has no text."""
    from app.services.simplification_service import SimplificationError
    
    mock_get_text.side_effect = SimplificationError(
        "No text available for policy pol_test123. Policy must be processed first.",
        details={"policy_id": "pol_test123", "status": "uploaded"}
    )
    
    response = await client.post(
        "/api/v1/simplification/explain",
        json={
            "policy_id": "pol_test123",
            "explanation_type": "explanation"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "no text available" in data["detail"]["message"].lower()


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_explain_policy_llm_error(mock_generate, mock_get_text, client):
    """Test 503 error when LLM service fails."""
    from app.services.llm_service import LLMError
    
    mock_get_text.return_value = ("Policy text...", "Policy Title")
    mock_generate.side_effect = LLMError(
        "LLM rate limit exceeded",
        details={"type": "rate_limit"}
    )
    
    response = await client.post(
        "/api/v1/simplification/explain",
        json={
            "policy_id": "pol_test123",
            "explanation_type": "explanation"
        }
    )
    
    assert response.status_code == 503
    data = response.json()
    assert "llm service error" in data["detail"]["message"].lower()


@pytest.mark.asyncio
async def test_explain_policy_invalid_request(client):
    """Test validation error with invalid request."""
    response = await client.post(
        "/api/v1/simplification/explain",
        json={
            # Missing required policy_id
            "explanation_type": "explanation"
        }
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
@patch('app.services.simplification_service.get_policy_text')
@patch('app.services.simplification_service.generate_completion')
async def test_explain_policy_with_custom_parameters(mock_generate, mock_get_text, client):
    """Test with custom temperature and model parameters."""
    mock_get_text.return_value = ("Policy text...", "Policy Title")
    mock_generate.return_value = "Simplified explanation..."
    
    response = await client.post(
        "/api/v1/simplification/explain",
        json={
            "policy_id": "pol_test123",
            "explanation_type": "explanation",
            "temperature": 0.5,
            "model": "gpt-4-turbo-preview",
            "focus_area": "eligibility criteria"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["model_used"] == "gpt-4-turbo-preview"


@pytest.mark.asyncio
async def test_simplification_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/api/v1/simplification/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "available_explanation_types" in data
    assert len(data["available_explanation_types"]) == 5
    assert "explanation" in data["available_explanation_types"]
    assert "eligibility" in data["available_explanation_types"]
