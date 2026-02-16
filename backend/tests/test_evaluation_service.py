"""
Tests for the evaluation service.
"""

import pytest
from app.services.evaluation_service import (
    calculate_relevance_score,
    calculate_coherence_score,
    calculate_completeness_score,
    check_source_grounding,
    detect_hallucination_risk,
    calculate_citation_quality,
    check_safety,
    evaluate_output
)


class TestRelevanceScore:
    """Tests for relevance score calculation."""
    
    def test_high_relevance(self):
        """Test high relevance when answer addresses query well."""
        query = "What are the income requirements for housing assistance?"
        answer = "The income requirements for housing assistance are 50% of median income."
        
        score = calculate_relevance_score(query, answer)
        assert score > 0.6, "Should have high relevance score"
    
    def test_low_relevance(self):
        """Test low relevance when answer doesn't address query."""
        query = "What are the income requirements?"
        answer = "The sky is blue and grass is green."
        
        score = calculate_relevance_score(query, answer)
        assert score < 0.3, "Should have low relevance score"
    
    def test_empty_inputs(self):
        """Test handling of empty inputs."""
        assert calculate_relevance_score("", "answer") == 0.0
        assert calculate_relevance_score("query", "") == 0.0


class TestCoherenceScore:
    """Tests for coherence score calculation."""
    
    def test_coherent_text(self):
        """Test coherent, well-structured text."""
        answer = "This is a well-written answer. It has proper sentences. Each sentence is clear and concise."
        
        score = calculate_coherence_score(answer)
        assert score > 0.7, "Should have high coherence score"
    
    def test_incoherent_text(self):
        """Test incoherent text with issues."""
        answer = "this is bad. no caps. word word word word word word word word word word"
        
        score = calculate_coherence_score(answer)
        assert score < 0.9, "Should have lower coherence score"
    
    def test_empty_text(self):
        """Test empty text."""
        assert calculate_coherence_score("") == 0.0


class TestCompletenessScore:
    """Tests for completeness score calculation."""
    
    def test_complete_answer(self):
        """Test complete, detailed answer."""
        query = "What are the requirements?"
        answer = "The requirements include: 1) Income below 50% median, 2) US citizenship, 3) No prior convictions. Therefore, you must meet all three criteria."
        
        score = calculate_completeness_score(answer, query)
        assert score > 0.8, "Should have high completeness score"
    
    def test_incomplete_answer(self):
        """Test incomplete, vague answer."""
        query = "What are the requirements?"
        answer = "Not sure."
        
        score = calculate_completeness_score(answer, query)
        assert score < 0.5, "Should have low completeness score"


class TestSourceGrounding:
    """Tests for source grounding checks."""
    
    def test_well_grounded(self):
        """Test answer well-grounded in sources."""
        answer = "The income limit is $50,000 per year according to the policy."
        sources = [
            {
                "chunk_text": "Applicants must have an annual income below $50,000 to qualify.",
                "policy_title": "Housing Policy"
            }
        ]
        
        score, flags = check_source_grounding(answer, sources)
        assert score > 0.3, "Should have decent grounding score"
        assert "no_sources_provided" not in flags
    
    def test_no_sources(self):
        """Test handling when no sources provided."""
        answer = "The income limit is $50,000."
        sources = []
        
        score, flags = check_source_grounding(answer, sources)
        assert score == 0.0
        assert "no_sources_provided" in flags
    
    def test_poorly_grounded(self):
        """Test answer not grounded in sources."""
        answer = "The income limit is $100,000 and you must be over 65 years old."
        sources = [
            {
                "chunk_text": "Applicants must have an annual income below $50,000.",
                "policy_title": "Housing Policy"
            }
        ]
        
        score, flags = check_source_grounding(answer, sources)
        # Score might be low due to mismatch
        assert isinstance(score, float)


class TestHallucinationDetection:
    """Tests for hallucination risk detection."""
    
    def test_low_risk(self):
        """Test low hallucination risk."""
        answer = "According to the document, the income limit is $50,000."
        sources = [
            {
                "chunk_text": "Income limit: $50,000 annually",
                "policy_title": "Policy"
            }
        ]
        
        risk = detect_hallucination_risk(answer, sources)
        assert risk in ["low", "medium"], "Should be low or medium risk"
    
    def test_high_risk(self):
        """Test high hallucination risk."""
        answer = "I think the income limit is probably around $75,000, but I'm not certain."
        sources = []
        
        risk = detect_hallucination_risk(answer, sources)
        assert risk in ["medium", "high"], "Should be medium or high risk"


class TestCitationQuality:
    """Tests for citation quality evaluation."""
    
    def test_good_citations(self):
        """Test answer with good citations."""
        answer = "According to Source 1, the income limit is $50,000. [Source 1] also mentions eligibility criteria."
        sources = [
            {"chunk_text": "Income limit: $50,000", "policy_title": "Policy"}
        ]
        
        score = calculate_citation_quality(answer, sources)
        assert score > 0.5, "Should have decent citation quality"
    
    def test_no_citations(self):
        """Test answer without citations."""
        answer = "The income limit is $50,000."
        sources = [
            {"chunk_text": "Income limit: $50,000", "policy_title": "Policy"}
        ]
        
        score = calculate_citation_quality(answer, sources)
        assert score < 0.5, "Should have low citation quality"


class TestSafetyChecks:
    """Tests for safety and bias detection."""
    
    def test_safe_content(self):
        """Test safe, unbiased content."""
        answer = "The policy applies to all eligible residents regardless of background."
        
        score, indicators = check_safety(answer)
        assert score >= 0.9, "Should have high safety score"
        assert len(indicators) == 0, "Should have no bias indicators"
    
    def test_biased_content(self):
        """Test content with bias indicators."""
        answer = "Young people always make poor financial decisions and can never manage money properly."
        
        score, indicators = check_safety(answer)
        assert score < 1.0, "Should have lower safety score"
        assert len(indicators) > 0, "Should detect bias indicators"


class TestEvaluateOutput:
    """Tests for comprehensive output evaluation."""
    
    def test_high_quality_output(self):
        """Test evaluation of high-quality output."""
        query = "What are the income requirements?"
        answer = "According to the housing policy, the income requirements are set at 50% of the area median income. This means that applicants must earn less than $50,000 annually to qualify for assistance."
        sources = [
            {
                "chunk_text": "Income requirements: 50% of area median income, approximately $50,000 annually",
                "policy_title": "Housing Assistance Policy",
                "chunk_id": 1,
                "policy_id": "pol_123"
            }
        ]
        
        result = evaluate_output(answer, query, sources)
        
        assert "relevance_score" in result
        assert "coherence_score" in result
        assert "overall_confidence" in result
        assert result["overall_confidence"] > 0.5, "Should have decent confidence"
        assert isinstance(result["quality_flags"], list)
    
    def test_low_quality_output(self):
        """Test evaluation of low-quality output."""
        query = "What are the income requirements?"
        answer = "idk"
        sources = []
        
        result = evaluate_output(answer, query, sources)
        
        assert result["overall_confidence"] < 0.5, "Should have low confidence"
        assert len(result["quality_flags"]) > 0, "Should have quality flags"
    
    def test_empty_answer(self):
        """Test evaluation of empty answer."""
        query = "What are the requirements?"
        answer = ""
        sources = []
        
        result = evaluate_output(answer, query, sources)
        
        assert result["overall_confidence"] == 0.0 or result["overall_confidence"] < 0.3
        assert "quality_flags" in result


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_very_long_answer(self):
        """Test evaluation of very long answer."""
        query = "Tell me about the policy"
        answer = "This is a policy. " * 500  # Very long, repetitive
        
        result = evaluate_output(answer, query, [])
        
        assert "coherence_score" in result
        # Repetitive text should be flagged
        assert result["coherence_score"] < 1.0
    
    def test_special_characters(self):
        """Test handling of special characters."""
        query = "What's the policy?"
        answer = "The policy states: 'Income < $50k' & residency = 2+ years!"
        
        result = evaluate_output(answer, query, [])
        
        assert "overall_confidence" in result
        assert isinstance(result["overall_confidence"], float)
    
    def test_multilingual_content(self):
        """Test handling of multilingual content."""
        query = "¿Cuáles son los requisitos?"
        answer = "Los requisitos incluyen ingresos bajos y residencia."
        
        result = evaluate_output(answer, query, [])
        
        assert "relevance_score" in result
        # Should still calculate metrics even for non-English
        assert isinstance(result["relevance_score"], float)
