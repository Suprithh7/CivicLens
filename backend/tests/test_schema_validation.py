"""
Unit tests for input validation on SimplificationRequest and RAGQueryRequest schemas.

Covers:
  - SimplificationRequest: blank/whitespace policy_id rejected
  - SimplificationRequest: explanation_type='eligibility' requires user_situation
  - SimplificationRequest: eligibility type with valid user_situation accepted
  - RAGQueryRequest: whitespace-only query rejected
  - RAGQueryRequest: valid query is stripped and accepted
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.simplification import SimplificationRequest, ExplanationType
from app.schemas.rag import RAGQueryRequest


# ===========================================================================
# SimplificationRequest
# ===========================================================================

class TestSimplificationRequestValidation:

    def test_valid_minimally_accepts(self):
        """A bare-minimum valid request (policy_id + default type) must pass."""
        req = SimplificationRequest(policy_id="pol_abc123")
        assert req.policy_id == "pol_abc123"
        assert req.explanation_type == ExplanationType.EXPLANATION

    def test_blank_policy_id_rejected(self):
        """An empty string policy_id must raise a ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SimplificationRequest(policy_id="")
        assert "policy_id" in str(exc_info.value)

    def test_whitespace_only_policy_id_rejected(self):
        """A whitespace-only policy_id must raise a ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            SimplificationRequest(policy_id="   ")
        assert "policy_id" in str(exc_info.value)

    def test_policy_id_is_stripped(self):
        """Leading/trailing whitespace around a valid ID should be stripped."""
        req = SimplificationRequest(policy_id="  pol_abc123  ")
        assert req.policy_id == "pol_abc123"

    def test_eligibility_type_without_user_situation_rejected(self):
        """explanation_type='eligibility' with no user_situation must fail."""
        with pytest.raises(ValidationError) as exc_info:
            SimplificationRequest(
                policy_id="pol_abc123",
                explanation_type="eligibility",
            )
        assert "user_situation" in str(exc_info.value)

    def test_eligibility_type_with_whitespace_user_situation_rejected(self):
        """explanation_type='eligibility' with whitespace-only user_situation must fail."""
        with pytest.raises(ValidationError) as exc_info:
            SimplificationRequest(
                policy_id="pol_abc123",
                explanation_type="eligibility",
                user_situation="   ",
            )
        assert "user_situation" in str(exc_info.value)

    def test_eligibility_type_with_valid_user_situation_accepted(self):
        """explanation_type='eligibility' with a real user_situation must pass."""
        req = SimplificationRequest(
            policy_id="pol_abc123",
            explanation_type="eligibility",
            user_situation="Single parent, $35k/year, two kids",
        )
        assert req.explanation_type == ExplanationType.ELIGIBILITY
        assert req.user_situation is not None

    def test_non_eligibility_type_without_user_situation_accepted(self):
        """Other explanation types do NOT require user_situation."""
        for t in [
            ExplanationType.EXPLANATION,
            ExplanationType.KEY_POINTS,
            ExplanationType.BENEFITS,
            ExplanationType.APPLICATION,
            ExplanationType.SCENARIO,
        ]:
            req = SimplificationRequest(policy_id="pol_abc123", explanation_type=t)
            assert req.explanation_type == t

    def test_temperature_bounds(self):
        """temperature must be 0.0–2.0."""
        with pytest.raises(ValidationError):
            SimplificationRequest(policy_id="pol_abc123", temperature=-0.1)
        with pytest.raises(ValidationError):
            SimplificationRequest(policy_id="pol_abc123", temperature=2.1)

    def test_max_points_bounds(self):
        """max_points must be 1–10."""
        with pytest.raises(ValidationError):
            SimplificationRequest(policy_id="pol_abc123", max_points=0)
        with pytest.raises(ValidationError):
            SimplificationRequest(policy_id="pol_abc123", max_points=11)


# ===========================================================================
# RAGQueryRequest
# ===========================================================================

class TestRAGQueryRequestValidation:

    def test_valid_query_accepted(self):
        """A normal query string must be accepted."""
        req = RAGQueryRequest(query="What are the income limits?")
        assert req.query == "What are the income limits?"

    def test_empty_query_rejected(self):
        """An empty string query must raise a ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RAGQueryRequest(query="")
        assert "query" in str(exc_info.value)

    def test_whitespace_only_query_rejected(self):
        """A whitespace-only query must raise a ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            RAGQueryRequest(query="   ")
        assert "query" in str(exc_info.value)

    def test_query_is_stripped(self):
        """Leading/trailing whitespace around a valid query should be stripped."""
        req = RAGQueryRequest(query="  What are the income limits?  ")
        assert req.query == "What are the income limits?"

    def test_query_too_long_rejected(self):
        """A query exceeding 1000 characters must be rejected."""
        with pytest.raises(ValidationError):
            RAGQueryRequest(query="x" * 1001)

    def test_top_k_bounds(self):
        """top_k must be 1–20."""
        with pytest.raises(ValidationError):
            RAGQueryRequest(query="valid?", top_k=0)
        with pytest.raises(ValidationError):
            RAGQueryRequest(query="valid?", top_k=21)

    def test_temperature_bounds(self):
        """temperature must be 0.0–2.0."""
        with pytest.raises(ValidationError):
            RAGQueryRequest(query="valid?", temperature=-0.1)
        with pytest.raises(ValidationError):
            RAGQueryRequest(query="valid?", temperature=2.1)

    def test_defaults_are_sane(self):
        """Default top_k and optional fields have expected defaults."""
        req = RAGQueryRequest(query="What is eligibility?")
        assert req.top_k == 5
        assert req.policy_id is None
        assert req.temperature is None
        assert req.model is None
        assert req.language is None
