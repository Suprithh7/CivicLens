"""
Unit tests for embedding service.
"""

import pytest
from app.services.embedding_service import (
    generate_embedding,
    generate_embeddings_batch,
    EmbeddingModel,
    EmbeddingError,
    EMBEDDING_DIMENSION
)


class TestEmbeddingGeneration:
    """Test embedding generation functions."""
    
    def test_generate_single_embedding(self):
        """Test generating a single embedding."""
        text = "This is a test policy document about healthcare."
        embedding = generate_embedding(text)
        
        # Check that embedding is a list
        assert isinstance(embedding, list)
        
        # Check embedding dimension
        assert len(embedding) == EMBEDDING_DIMENSION
        
        # Check that all values are floats
        assert all(isinstance(x, float) for x in embedding)
    
    def test_generate_embedding_empty_text(self):
        """Test that empty text raises an error."""
        with pytest.raises(EmbeddingError) as exc_info:
            generate_embedding("")
        
        assert "empty text" in str(exc_info.value.message).lower()
    
    def test_generate_batch_embeddings(self):
        """Test generating embeddings in batch."""
        texts = [
            "Healthcare policy for rural areas.",
            "Education reform initiative.",
            "Infrastructure development plan."
        ]
        
        embeddings = generate_embeddings_batch(texts)
        
        # Check that we get the right number of embeddings
        assert len(embeddings) == len(texts)
        
        # Check each embedding
        for embedding in embeddings:
            assert isinstance(embedding, list)
            assert len(embedding) == EMBEDDING_DIMENSION
            assert all(isinstance(x, float) for x in embedding)
    
    def test_generate_batch_embeddings_empty_list(self):
        """Test that empty list returns empty list."""
        embeddings = generate_embeddings_batch([])
        assert embeddings == []
    
    def test_generate_batch_embeddings_with_empty_texts(self):
        """Test that list with only empty texts raises error."""
        with pytest.raises(EmbeddingError):
            generate_embeddings_batch(["", "   ", ""])
    
    def test_embedding_model_singleton(self):
        """Test that EmbeddingModel is a singleton."""
        model1 = EmbeddingModel()
        model2 = EmbeddingModel()
        
        # Should be the same instance
        assert model1 is model2
    
    def test_embedding_consistency(self):
        """Test that same text produces same embedding."""
        text = "Consistent policy text for testing."
        
        embedding1 = generate_embedding(text)
        embedding2 = generate_embedding(text)
        
        # Embeddings should be identical for the same text
        assert embedding1 == embedding2
    
    def test_different_texts_different_embeddings(self):
        """Test that different texts produce different embeddings."""
        text1 = "Healthcare policy for urban areas."
        text2 = "Education policy for rural schools."
        
        embedding1 = generate_embedding(text1)
        embedding2 = generate_embedding(text2)
        
        # Embeddings should be different
        assert embedding1 != embedding2
    
    def test_batch_size_parameter(self):
        """Test that batch_size parameter works."""
        texts = ["Text " + str(i) for i in range(10)]
        
        # Should work with different batch sizes
        embeddings1 = generate_embeddings_batch(texts, batch_size=2)
        embeddings2 = generate_embeddings_batch(texts, batch_size=5)
        
        # Results should be the same regardless of batch size
        assert len(embeddings1) == len(embeddings2) == len(texts)
        
        # Each corresponding embedding should be identical
        for emb1, emb2 in zip(embeddings1, embeddings2):
            assert emb1 == emb2


# Note: Integration tests for process_policy_embeddings would require
# database setup and are better suited for integration test suite
