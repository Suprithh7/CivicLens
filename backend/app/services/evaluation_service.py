"""
AI Output Evaluation Service.
Provides quality, consistency, and safety checks for LLM-generated outputs.
"""

import logging
import re
from typing import Dict, List, Optional, Set
from datetime import datetime
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class EvaluationMetrics:
    """Container for evaluation metrics."""
    
    def __init__(self):
        self.relevance_score: float = 0.0
        self.coherence_score: float = 0.0
        self.completeness_score: float = 0.0
        self.source_grounding_score: float = 0.0
        self.hallucination_risk: str = "low"  # low, medium, high
        self.citation_quality: float = 0.0
        self.safety_score: float = 1.0  # 1.0 = safe, lower = potential issues
        self.bias_indicators: List[str] = []
        self.quality_flags: List[str] = []
        self.overall_confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            "relevance_score": round(self.relevance_score, 2),
            "coherence_score": round(self.coherence_score, 2),
            "completeness_score": round(self.completeness_score, 2),
            "source_grounding_score": round(self.source_grounding_score, 2),
            "hallucination_risk": self.hallucination_risk,
            "citation_quality": round(self.citation_quality, 2),
            "safety_score": round(self.safety_score, 2),
            "bias_indicators": self.bias_indicators,
            "quality_flags": self.quality_flags,
            "overall_confidence": round(self.overall_confidence, 2)
        }


def calculate_relevance_score(
    query: str,
    answer: str,
    sources: Optional[List[Dict]] = None
) -> float:
    """
    Calculate how relevant the answer is to the query.
    
    Args:
        query: User's question
        answer: Generated answer
        sources: Retrieved source chunks (optional)
        
    Returns:
        Relevance score between 0.0 and 1.0
    """
    if not answer or not query:
        return 0.0
    
    # Extract keywords from query (remove stop words)
    stop_words = {
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'what', 'when', 'where',
        'who', 'why', 'how', 'can', 'could', 'would', 'should', 'do', 'does',
        'did', 'have', 'has', 'had', 'be', 'been', 'being', 'in', 'on', 'at',
        'to', 'for', 'of', 'with', 'by', 'from', 'about', 'as', 'into', 'through'
    }
    
    query_words = set(
        word.lower() 
        for word in re.findall(r'\b\w+\b', query)
        if word.lower() not in stop_words and len(word) > 2
    )
    
    answer_lower = answer.lower()
    
    # Count keyword matches
    matched_keywords = sum(1 for word in query_words if word in answer_lower)
    
    if not query_words:
        return 0.5  # Neutral score if no meaningful keywords
    
    keyword_coverage = matched_keywords / len(query_words)
    
    # Check for direct question addressing
    question_indicators = ['yes', 'no', 'according to', 'based on', 'the answer is']
    has_direct_answer = any(indicator in answer_lower for indicator in question_indicators)
    
    # Combine metrics
    base_score = keyword_coverage * 0.7
    if has_direct_answer:
        base_score += 0.3
    
    return min(1.0, base_score)


def calculate_coherence_score(answer: str) -> float:
    """
    Calculate the coherence and readability of the answer.
    
    Args:
        answer: Generated answer
        
    Returns:
        Coherence score between 0.0 and 1.0
    """
    if not answer:
        return 0.0
    
    score = 1.0
    flags = []
    
    # Check for proper sentence structure
    sentences = re.split(r'[.!?]+', answer)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) == 0:
        return 0.0
    
    # Check sentence length (too short or too long reduces coherence)
    avg_sentence_length = len(answer) / len(sentences)
    if avg_sentence_length < 20:
        score -= 0.1
        flags.append("very_short_sentences")
    elif avg_sentence_length > 200:
        score -= 0.1
        flags.append("very_long_sentences")
    
    # Check for incomplete sentences (sentences starting with lowercase)
    incomplete_sentences = sum(
        1 for s in sentences 
        if s and s[0].islower() and not s.startswith('e.g.') and not s.startswith('i.e.')
    )
    if incomplete_sentences > len(sentences) * 0.2:
        score -= 0.2
        flags.append("incomplete_sentences")
    
    # Check for repetition
    words = answer.lower().split()
    if len(words) > 10:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.5:
            score -= 0.2
            flags.append("high_repetition")
    
    # Check for proper capitalization
    if answer and answer[0].islower():
        score -= 0.1
        flags.append("improper_capitalization")
    
    # Check for excessive punctuation
    punct_ratio = sum(1 for c in answer if c in '!?') / max(len(answer), 1)
    if punct_ratio > 0.05:
        score -= 0.1
        flags.append("excessive_punctuation")
    
    return max(0.0, score)


def calculate_completeness_score(
    answer: str,
    query: str,
    min_length: int = 50
) -> float:
    """
    Calculate whether the answer provides sufficient detail.
    
    Args:
        answer: Generated answer
        query: User's question
        min_length: Minimum expected answer length
        
    Returns:
        Completeness score between 0.0 and 1.0
    """
    if not answer:
        return 0.0
    
    score = 1.0
    
    # Check length
    if len(answer) < min_length:
        score -= 0.3
    
    # Check for vague responses
    vague_phrases = [
        'i don\'t know',
        'not sure',
        'unclear',
        'cannot determine',
        'no information',
        'not available',
        'not found'
    ]
    
    answer_lower = answer.lower()
    vague_count = sum(1 for phrase in vague_phrases if phrase in answer_lower)
    
    if vague_count > 0:
        # Vague responses are acceptable if acknowledged properly
        if len(answer) < 100:
            score -= 0.2  # Very short vague answer
    
    # Check for structured information (lists, numbers, etc.)
    has_structure = bool(
        re.search(r'\d+\.|\*|-|•', answer) or  # Bullet points or numbered lists
        re.search(r'\d+', answer)  # Numbers/statistics
    )
    
    if has_structure:
        score += 0.1
    
    # Check for explanatory content
    explanatory_words = ['because', 'therefore', 'thus', 'since', 'as a result', 'due to']
    has_explanation = any(word in answer_lower for word in explanatory_words)
    
    if has_explanation:
        score += 0.1
    
    return min(1.0, max(0.0, score))


def check_source_grounding(
    answer: str,
    sources: List[Dict]
) -> tuple[float, List[str]]:
    """
    Check if claims in the answer are grounded in source documents.
    
    Args:
        answer: Generated answer
        sources: Retrieved source chunks
        
    Returns:
        Tuple of (grounding_score, quality_flags)
    """
    if not sources:
        return 0.0, ["no_sources_provided"]
    
    if not answer:
        return 0.0, ["empty_answer"]
    
    flags = []
    
    # Combine all source texts
    source_text = " ".join(
        source.get("chunk_text", "") 
        for source in sources
    ).lower()
    
    if not source_text:
        return 0.0, ["empty_sources"]
    
    # Extract factual claims from answer (sentences with specific information)
    sentences = re.split(r'[.!?]+', answer)
    factual_sentences = [
        s.strip() for s in sentences
        if s.strip() and (
            re.search(r'\d+', s) or  # Contains numbers
            len(s.split()) > 5  # Substantial sentence
        )
    ]
    
    if not factual_sentences:
        return 0.5, ["no_factual_claims"]  # Neutral score
    
    # Check how many factual claims have support in sources
    grounded_count = 0
    for sentence in factual_sentences:
        # Extract key phrases (3+ word sequences)
        words = sentence.lower().split()
        if len(words) < 3:
            continue
        
        # Check for phrase overlap with sources
        max_overlap = 0
        for i in range(len(words) - 2):
            phrase = " ".join(words[i:i+3])
            if phrase in source_text:
                max_overlap = max(max_overlap, 3)
        
        # Also check for semantic similarity using sequence matcher
        similarity = SequenceMatcher(None, sentence.lower(), source_text).ratio()
        
        if max_overlap >= 3 or similarity > 0.3:
            grounded_count += 1
    
    grounding_score = grounded_count / len(factual_sentences) if factual_sentences else 0.5
    
    # Check for citation markers
    has_citations = bool(re.search(r'\[source \d+\]|source \d+:|according to', answer.lower()))
    
    if has_citations:
        grounding_score = min(1.0, grounding_score + 0.1)
    else:
        flags.append("no_explicit_citations")
    
    if grounding_score < 0.3:
        flags.append("low_source_grounding")
    
    return grounding_score, flags


def detect_hallucination_risk(
    answer: str,
    sources: List[Dict]
) -> str:
    """
    Detect potential hallucination in the answer.
    
    Args:
        answer: Generated answer
        sources: Retrieved source chunks
        
    Returns:
        Risk level: "low", "medium", or "high"
    """
    if not answer:
        return "low"
    
    answer_lower = answer.lower()
    
    # High-risk indicators
    high_risk_patterns = [
        r'i think',
        r'in my opinion',
        r'i believe',
        r'probably',
        r'most likely',
        r'it seems like',
        r'i would guess'
    ]
    
    high_risk_count = sum(
        1 for pattern in high_risk_patterns
        if re.search(pattern, answer_lower)
    )
    
    # Check for specific numbers/dates without source grounding
    has_specific_data = bool(re.search(r'\$\d+|€\d+|\d{4}|\d+%|\d+ (years|months|days)', answer))
    
    if has_specific_data and not sources:
        return "high"
    
    # Check source grounding
    grounding_score, _ = check_source_grounding(answer, sources)
    
    if high_risk_count >= 2:
        return "high"
    elif high_risk_count == 1 or grounding_score < 0.4:
        return "medium"
    else:
        return "low"


def calculate_citation_quality(answer: str, sources: List[Dict]) -> float:
    """
    Evaluate the quality of citations in the answer.
    
    Args:
        answer: Generated answer
        sources: Retrieved source chunks
        
    Returns:
        Citation quality score between 0.0 and 1.0
    """
    if not sources:
        return 0.0
    
    if not answer:
        return 0.0
    
    score = 0.0
    
    # Check for explicit source references
    source_refs = re.findall(r'\[source \d+\]|source \d+:', answer.lower())
    
    if source_refs:
        score += 0.5
        
        # Check if all sources are cited
        cited_sources = set()
        for ref in source_refs:
            match = re.search(r'\d+', ref)
            if match:
                cited_sources.add(int(match.group()))
        
        citation_coverage = len(cited_sources) / len(sources)
        score += citation_coverage * 0.3
    
    # Check for attribution phrases
    attribution_phrases = ['according to', 'based on', 'as stated in', 'the document mentions']
    has_attribution = any(phrase in answer.lower() for phrase in attribution_phrases)
    
    if has_attribution:
        score += 0.2
    
    return min(1.0, score)


def check_safety(answer: str) -> tuple[float, List[str]]:
    """
    Check for harmful content or bias in the answer.
    
    Args:
        answer: Generated answer
        
    Returns:
        Tuple of (safety_score, bias_indicators)
    """
    if not answer:
        return 1.0, []
    
    safety_score = 1.0
    bias_indicators = []
    
    answer_lower = answer.lower()
    
    # Check for harmful content patterns
    harmful_patterns = [
        r'you should lie',
        r'illegal',
        r'commit fraud',
        r'deceive',
        r'cheat the system'
    ]
    
    for pattern in harmful_patterns:
        if re.search(pattern, answer_lower):
            safety_score -= 0.3
            bias_indicators.append("potentially_harmful_advice")
            break
    
    # Check for bias indicators
    bias_patterns = {
        'gender_bias': [r'\b(he|she) (always|never|typically)\b', r'(men|women) (are|tend to)'],
        'age_bias': [r'(young|old) people (are|always|never)', r'(elderly|youth) (can\'t|cannot)'],
        'socioeconomic_bias': [r'poor people', r'rich people', r'lower class', r'upper class']
    }
    
    for bias_type, patterns in bias_patterns.items():
        for pattern in patterns:
            if re.search(pattern, answer_lower):
                bias_indicators.append(bias_type)
                safety_score -= 0.1
                break
    
    # Check for absolute statements (can indicate bias)
    absolute_words = ['always', 'never', 'all', 'none', 'every', 'no one']
    absolute_count = sum(1 for word in absolute_words if f' {word} ' in f' {answer_lower} ')
    
    if absolute_count > 3:
        bias_indicators.append("excessive_absolutes")
        safety_score -= 0.1
    
    return max(0.0, safety_score), list(set(bias_indicators))


def evaluate_output(
    answer: str,
    query: str,
    sources: Optional[List[Dict]] = None,
    context: Optional[Dict] = None
) -> Dict:
    """
    Comprehensive evaluation of AI-generated output.
    
    Args:
        answer: Generated answer
        query: User's question
        sources: Retrieved source chunks (optional)
        context: Additional context (e.g., policy_text for simplification)
        
    Returns:
        Dictionary with evaluation metrics and flags
    """
    logger.info(f"Evaluating output for query: '{query[:50]}...'")
    
    metrics = EvaluationMetrics()
    sources = sources or []
    
    # Quality Metrics
    metrics.relevance_score = calculate_relevance_score(query, answer, sources)
    metrics.coherence_score = calculate_coherence_score(answer)
    metrics.completeness_score = calculate_completeness_score(answer, query)
    
    # Factual Consistency
    if sources:
        grounding_score, grounding_flags = check_source_grounding(answer, sources)
        metrics.source_grounding_score = grounding_score
        metrics.quality_flags.extend(grounding_flags)
        
        metrics.hallucination_risk = detect_hallucination_risk(answer, sources)
        metrics.citation_quality = calculate_citation_quality(answer, sources)
    else:
        metrics.source_grounding_score = 0.0
        metrics.hallucination_risk = "medium"
        metrics.citation_quality = 0.0
        metrics.quality_flags.append("no_sources")
    
    # Safety Checks
    safety_score, bias_indicators = check_safety(answer)
    metrics.safety_score = safety_score
    metrics.bias_indicators = bias_indicators
    
    # Calculate overall confidence
    # Weight: relevance (25%), coherence (20%), completeness (20%), 
    # grounding (25%), safety (10%)
    metrics.overall_confidence = (
        metrics.relevance_score * 0.25 +
        metrics.coherence_score * 0.20 +
        metrics.completeness_score * 0.20 +
        metrics.source_grounding_score * 0.25 +
        metrics.safety_score * 0.10
    )
    
    # Add quality flags based on scores
    if metrics.relevance_score < 0.5:
        metrics.quality_flags.append("low_relevance")
    if metrics.coherence_score < 0.6:
        metrics.quality_flags.append("low_coherence")
    if metrics.completeness_score < 0.5:
        metrics.quality_flags.append("incomplete_answer")
    if metrics.hallucination_risk == "high":
        metrics.quality_flags.append("high_hallucination_risk")
    if metrics.safety_score < 0.8:
        metrics.quality_flags.append("safety_concern")
    
    # Remove duplicates
    metrics.quality_flags = list(set(metrics.quality_flags))
    
    logger.info(
        f"Evaluation complete: confidence={metrics.overall_confidence:.2f}, "
        f"flags={len(metrics.quality_flags)}"
    )
    
    return metrics.to_dict()
