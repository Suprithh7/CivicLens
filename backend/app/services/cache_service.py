"""
Cache service for AI/LLM responses.
Provides in-memory caching with TTL to reduce API costs and improve latency.
"""

import logging
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# Cache configuration
SIMPLIFICATION_CACHE_SIZE = 1000  # Store up to 1000 simplifications
SIMPLIFICATION_TTL = 24 * 3600    # 24 hours
RAG_CACHE_SIZE = 500              # Store up to 500 RAG responses
RAG_CACHE_TTL = 1 * 3600          # 1 hour

# Global caches with TTL
_simplification_cache = TTLCache(maxsize=SIMPLIFICATION_CACHE_SIZE, ttl=SIMPLIFICATION_TTL)
_rag_cache = TTLCache(maxsize=RAG_CACHE_SIZE, ttl=RAG_CACHE_TTL)

# Cache statistics
_cache_stats = {
    "simplification_hits": 0,
    "simplification_misses": 0,
    "rag_hits": 0,
    "rag_misses": 0
}


def generate_cache_key(data: Dict[str, Any]) -> str:
    """
    Generate deterministic cache key from data.
    
    Args:
        data: Dictionary of parameters to hash
        
    Returns:
        SHA256 hash of sorted JSON representation
    """
    # Sort keys for consistency and filter out None values
    filtered_data = {k: v for k, v in data.items() if v is not None}
    sorted_data = json.dumps(filtered_data, sort_keys=True)
    return hashlib.sha256(sorted_data.encode()).hexdigest()


def get_simplification_cache(key: str) -> Optional[Dict]:
    """
    Get cached simplification response.
    
    Args:
        key: Cache key
        
    Returns:
        Cached response dictionary or None if not found
    """
    result = _simplification_cache.get(key)
    if result:
        _cache_stats["simplification_hits"] += 1
        logger.info(f"Simplification cache HIT (key: {key[:16]}...)")
    else:
        _cache_stats["simplification_misses"] += 1
        logger.info(f"Simplification cache MISS (key: {key[:16]}...)")
    return result


def set_simplification_cache(key: str, value: Dict) -> None:
    """
    Store simplification response in cache.
    
    Args:
        key: Cache key
        value: Response dictionary to cache
    """
    _simplification_cache[key] = value
    logger.info(f"Stored simplification in cache (key: {key[:16]}...)")


def get_rag_cache(key: str) -> Optional[Dict]:
    """
    Get cached RAG response.
    
    Args:
        key: Cache key
        
    Returns:
        Cached response dictionary or None if not found
    """
    result = _rag_cache.get(key)
    if result:
        _cache_stats["rag_hits"] += 1
        logger.info(f"RAG cache HIT (key: {key[:16]}...)")
    else:
        _cache_stats["rag_misses"] += 1
        logger.info(f"RAG cache MISS (key: {key[:16]}...)")
    return result


def set_rag_cache(key: str, value: Dict) -> None:
    """
    Store RAG response in cache.
    
    Args:
        key: Cache key
        value: Response dictionary to cache
    """
    _rag_cache[key] = value
    logger.info(f"Stored RAG response in cache (key: {key[:16]}...)")


def get_cache_stats() -> Dict:
    """
    Get cache statistics including hit rates and sizes.
    
    Returns:
        Dictionary with cache statistics for both caches
    """
    total_simplification = _cache_stats["simplification_hits"] + _cache_stats["simplification_misses"]
    total_rag = _cache_stats["rag_hits"] + _cache_stats["rag_misses"]
    
    simplification_hit_rate = (
        _cache_stats["simplification_hits"] / total_simplification 
        if total_simplification > 0 else 0
    )
    rag_hit_rate = (
        _cache_stats["rag_hits"] / total_rag 
        if total_rag > 0 else 0
    )
    
    # Calculate estimated cost savings (assuming $0.002 per 1K tokens, ~500 tokens avg)
    avg_cost_per_call = 0.001  # $0.001 per call estimate
    simplification_savings = _cache_stats["simplification_hits"] * avg_cost_per_call
    rag_savings = _cache_stats["rag_hits"] * avg_cost_per_call
    
    return {
        "simplification": {
            "hits": _cache_stats["simplification_hits"],
            "misses": _cache_stats["simplification_misses"],
            "total_requests": total_simplification,
            "hit_rate": round(simplification_hit_rate, 4),
            "hit_rate_percent": round(simplification_hit_rate * 100, 2),
            "cache_size": len(_simplification_cache),
            "max_size": _simplification_cache.maxsize,
            "estimated_savings_usd": round(simplification_savings, 4)
        },
        "rag": {
            "hits": _cache_stats["rag_hits"],
            "misses": _cache_stats["rag_misses"],
            "total_requests": total_rag,
            "hit_rate": round(rag_hit_rate, 4),
            "hit_rate_percent": round(rag_hit_rate * 100, 2),
            "cache_size": len(_rag_cache),
            "max_size": _rag_cache.maxsize,
            "estimated_savings_usd": round(rag_savings, 4)
        },
        "total": {
            "total_hits": _cache_stats["simplification_hits"] + _cache_stats["rag_hits"],
            "total_requests": total_simplification + total_rag,
            "estimated_total_savings_usd": round(simplification_savings + rag_savings, 4)
        }
    }


def clear_cache(cache_type: str = "all") -> Dict:
    """
    Clear cache(s).
    
    Args:
        cache_type: Type of cache to clear ("simplification", "rag", or "all")
        
    Returns:
        Dictionary with cleared cache information
    """
    cleared = []
    
    if cache_type in ["all", "simplification"]:
        size_before = len(_simplification_cache)
        _simplification_cache.clear()
        cleared.append(f"simplification ({size_before} entries)")
        logger.info(f"Cleared simplification cache ({size_before} entries)")
    
    if cache_type in ["all", "rag"]:
        size_before = len(_rag_cache)
        _rag_cache.clear()
        cleared.append(f"rag ({size_before} entries)")
        logger.info(f"Cleared RAG cache ({size_before} entries)")
    
    return {
        "message": f"Cache cleared: {', '.join(cleared)}",
        "cache_type": cache_type
    }


def invalidate_policy_cache(policy_id: str) -> Dict:
    """
    Invalidate all cached responses for a specific policy.
    
    Note: Current implementation clears entire simplification cache.
    Future enhancement: Track keys by policy_id for selective invalidation.
    
    Args:
        policy_id: Policy identifier
        
    Returns:
        Dictionary with invalidation information
    """
    logger.warning(
        f"Invalidating cache for policy {policy_id} - clearing entire simplification cache"
    )
    return clear_cache("simplification")
