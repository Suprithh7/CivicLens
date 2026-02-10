"""
Unit tests for FAISS service.
"""

import pytest
import numpy as np
from app.services.faiss_service import FAISSIndexManager, FAISSError


class TestFAISSIndexManager:
    """Test FAISS index management."""
    
    def test_build_index(self):
        """Test building a FAISS index."""
        manager = FAISSIndexManager(dimension=384)
        
        # Create sample embeddings
        embeddings = np.random.rand(10, 384).astype('float32')
        chunk_ids = list(range(10))
        
        # Build index
        index = manager.build_index("test_policy", embeddings, chunk_ids)
        
        # Verify index
        assert index.ntotal == 10
        assert "test_policy" in manager.indices
        assert "test_policy" in manager.id_maps
    
    def test_build_index_dimension_mismatch(self):
        """Test that dimension mismatch raises error."""
        manager = FAISSIndexManager(dimension=384)
        
        # Wrong dimension
        embeddings = np.random.rand(10, 256).astype('float32')
        chunk_ids = list(range(10))
        
        with pytest.raises(FAISSError) as exc_info:
            manager.build_index("test_policy", embeddings, chunk_ids)
        
        assert "dimension mismatch" in str(exc_info.value.message).lower()
    
    def test_build_index_count_mismatch(self):
        """Test that count mismatch raises error."""
        manager = FAISSIndexManager(dimension=384)
        
        embeddings = np.random.rand(10, 384).astype('float32')
        chunk_ids = list(range(5))  # Wrong count
        
        with pytest.raises(FAISSError) as exc_info:
            manager.build_index("test_policy", embeddings, chunk_ids)
        
        assert "must match" in str(exc_info.value.message).lower()
    
    def test_search(self):
        """Test searching the index."""
        manager = FAISSIndexManager(dimension=384)
        
        # Build index
        embeddings = np.random.rand(10, 384).astype('float32')
        chunk_ids = list(range(100, 110))  # Use non-sequential IDs
        manager.build_index("test_policy", embeddings, chunk_ids)
        
        # Search with first embedding
        query = embeddings[0]
        result_ids, distances = manager.search("test_policy", query, top_k=3)
        
        # First result should be the query itself (distance ~0)
        assert len(result_ids) == 3
        assert result_ids[0] == 100  # First chunk ID
        assert distances[0] < 0.01  # Very small distance
    
    def test_save_and_load_index(self, tmp_path):
        """Test saving and loading index."""
        # Override index directory for testing
        import app.services.faiss_service as faiss_module
        original_dir = faiss_module.FAISS_INDEX_DIR
        faiss_module.FAISS_INDEX_DIR = tmp_path
        
        try:
            manager = FAISSIndexManager(dimension=384)
            
            # Build and save index
            embeddings = np.random.rand(5, 384).astype('float32')
            chunk_ids = list(range(5))
            manager.build_index("test_policy", embeddings, chunk_ids)
            manager.save_index("test_policy")
            
            # Create new manager and load
            new_manager = FAISSIndexManager(dimension=384)
            loaded_index = new_manager.load_index("test_policy")
            
            # Verify loaded index
            assert loaded_index.ntotal == 5
            assert new_manager.id_maps["test_policy"] == chunk_ids
            
        finally:
            # Restore original directory
            faiss_module.FAISS_INDEX_DIR = original_dir
    
    def test_delete_index(self, tmp_path):
        """Test deleting index."""
        import app.services.faiss_service as faiss_module
        original_dir = faiss_module.FAISS_INDEX_DIR
        faiss_module.FAISS_INDEX_DIR = tmp_path
        
        try:
            manager = FAISSIndexManager(dimension=384)
            
            # Build and save index
            embeddings = np.random.rand(3, 384).astype('float32')
            chunk_ids = list(range(3))
            manager.build_index("test_policy", embeddings, chunk_ids)
            manager.save_index("test_policy")
            
            # Delete index
            manager.delete_index("test_policy")
            
            # Verify deletion
            assert "test_policy" not in manager.indices
            assert "test_policy" not in manager.id_maps
            assert not manager._get_index_path("test_policy").exists()
            
        finally:
            faiss_module.FAISS_INDEX_DIR = original_dir
    
    def test_search_similarity_ordering(self):
        """Test that search results are ordered by similarity."""
        manager = FAISSIndexManager(dimension=384)
        
        # Create embeddings with known relationships
        base = np.random.rand(384).astype('float32')
        embeddings = np.array([
            base,  # Identical
            base + 0.1,  # Similar
            base + 0.5,  # Less similar
            np.random.rand(384).astype('float32'),  # Random
        ], dtype='float32')
        
        chunk_ids = [10, 20, 30, 40]
        manager.build_index("test_policy", embeddings, chunk_ids)
        
        # Search with base
        result_ids, distances = manager.search("test_policy", base, top_k=4)
        
        # Distances should be in ascending order
        assert distances[0] < distances[1] < distances[2] < distances[3]
        assert result_ids[0] == 10  # First should be identical
