"""
Tests for cache service functionality.
"""

import pytest
from app.services.cache_service import (
    generate_cache_key,
    get_simplification_cache,
    set_simplification_cache,
    get_rag_cache,
    set_rag_cache,
    get_cache_stats,
    clear_cache
)


def test_generate_cache_key_deterministic():
    """Test that cache key generation is deterministic."""
    data1 = {"policy_id": "pol_123", "explanation_type": "key_points", "language": "en"}
    data2 = {"policy_id": "pol_123", "explanation_type": "key_points", "language": "en"}
    
    key1 = generate_cache_key(data1)
    key2 = generate_cache_key(data2)
    
    assert key1 == key2


def test_generate_cache_key_order_independent():
    """Test that cache key is independent of key order."""
    data1 = {"a": "1", "b": "2", "c": "3"}
    data2 = {"c": "3", "a": "1", "b": "2"}
    
    key1 = generate_cache_key(data1)
    key2 = generate_cache_key(data2)
    
    assert key1 == key2


def test_generate_cache_key_filters_none():
    """Test that None values are filtered out."""
    data1 = {"policy_id": "pol_123", "language": "en", "scenario": None}
    data2 = {"policy_id": "pol_123", "language": "en"}
    
    key1 = generate_cache_key(data1)
    key2 = generate_cache_key(data2)
    
    assert key1 == key2


def test_simplification_cache_hit():
    """Test simplification cache hit."""
    clear_cache("simplification")
    
    key = "test_key_123"
    value = {"policy_id": "pol_123", "simplified_text": "Test response"}
    
    # Store in cache
    set_simplification_cache(key, value)
    
    # Retrieve from cache
    cached = get_simplification_cache(key)
    
    assert cached is not None
    assert cached["policy_id"] == "pol_123"
    assert cached["simplified_text"] == "Test response"


def test_simplification_cache_miss():
    """Test simplification cache miss."""
    clear_cache("simplification")
    
    key = "nonexistent_key"
    cached = get_simplification_cache(key)
    
    assert cached is None


def test_rag_cache_hit():
    """Test RAG cache hit."""
    clear_cache("rag")
    
    key = "rag_test_key"
    value = {"query": "What is this policy?", "answer": "Test answer"}
    
    # Store in cache
    set_rag_cache(key, value)
    
    # Retrieve from cache
    cached = get_rag_cache(key)
    
    assert cached is not None
    assert cached["query"] == "What is this policy?"
    assert cached["answer"] == "Test answer"


def test_cache_statistics():
    """Test cache statistics tracking."""
    clear_cache("all")
    
    # Generate some cache hits and misses
    set_simplification_cache("key1", {"data": "value1"})
    get_simplification_cache("key1")  # Hit
    get_simplification_cache("key2")  # Miss
    
    set_rag_cache("rag_key1", {"data": "rag_value1"})
    get_rag_cache("rag_key1")  # Hit
    get_rag_cache("rag_key2")  # Miss
    
    stats = get_cache_stats()
    
    assert stats["simplification"]["hits"] >= 1
    assert stats["simplification"]["misses"] >= 1
    assert stats["rag"]["hits"] >= 1
    assert stats["rag"]["misses"] >= 1
    assert "hit_rate" in stats["simplification"]
    assert "estimated_savings_usd" in stats["simplification"]


def test_clear_cache_simplification():
    """Test clearing simplification cache."""
    clear_cache("all")
    
    set_simplification_cache("key1", {"data": "value1"})
    set_simplification_cache("key2", {"data": "value2"})
    
    result = clear_cache("simplification")
    
    assert "simplification" in result["message"]
    assert get_simplification_cache("key1") is None
    assert get_simplification_cache("key2") is None


def test_clear_cache_rag():
    """Test clearing RAG cache."""
    clear_cache("all")
    
    set_rag_cache("key1", {"data": "value1"})
    set_rag_cache("key2", {"data": "value2"})
    
    result = clear_cache("rag")
    
    assert "rag" in result["message"]
    assert get_rag_cache("key1") is None
    assert get_rag_cache("key2") is None


def test_clear_cache_all():
    """Test clearing all caches."""
    set_simplification_cache("simp_key", {"data": "simp_value"})
    set_rag_cache("rag_key", {"data": "rag_value"})
    
    result = clear_cache("all")
    
    assert "simplification" in result["message"]
    assert "rag" in result["message"]
    assert get_simplification_cache("simp_key") is None
    assert get_rag_cache("rag_key") is None


def test_cache_hit_rate_calculation():
    """Test cache hit rate calculation."""
    clear_cache("all")
    
    # Create 3 hits and 1 miss (75% hit rate)
    set_simplification_cache("key1", {"data": "value1"})
    get_simplification_cache("key1")  # Hit
    get_simplification_cache("key1")  # Hit
    get_simplification_cache("key1")  # Hit
    get_simplification_cache("key2")  # Miss
    
    stats = get_cache_stats()
    
    assert stats["simplification"]["total_requests"] == 4
    assert stats["simplification"]["hits"] == 3
    assert stats["simplification"]["misses"] == 1
    assert stats["simplification"]["hit_rate"] == 0.75
    assert stats["simplification"]["hit_rate_percent"] == 75.0
