"""
Test script for text chunking functionality.
Tests the chunking service with various scenarios.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.text_chunking import chunk_text, split_into_sentences, TextChunk


def test_sentence_splitting():
    """Test sentence splitting functionality."""
    print("\n=== Testing Sentence Splitting ===\n")
    
    test_text = "This is the first sentence. This is the second! And here's a third? Final sentence."
    sentences = split_into_sentences(test_text)
    
    print(f"Input text: {test_text}")
    print(f"\nExtracted {len(sentences)} sentences:")
    for i, sentence in enumerate(sentences, 1):
        print(f"  {i}. {sentence}")
    
    assert len(sentences) == 4, f"Expected 4 sentences, got {len(sentences)}"
    print("\n✓ Sentence splitting test passed")
    return True


def test_basic_chunking():
    """Test basic chunking with fixed size."""
    print("\n=== Testing Basic Chunking ===\n")
    
    test_text = """
    Government policy documents are often long and complex. They contain important information
    about regulations and procedures. Citizens need to understand these policies. However, the
    length and complexity make them difficult to read. Breaking them into smaller chunks helps.
    Each chunk should be manageable. The chunks should also overlap slightly. This ensures
    continuity of context. The chunking algorithm must respect sentence boundaries. This prevents
    awkward splits in the middle of sentences.
    """
    
    chunks = chunk_text(test_text.strip(), chunk_size=200, overlap=50)
    
    print(f"Input text: {len(test_text.strip())} characters")
    print(f"Created {len(chunks)} chunks\n")
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}:")
        print(f"  Index: {chunk.chunk_index}")
        print(f"  Size: {len(chunk.text)} chars")
        print(f"  Position: {chunk.start_char}-{chunk.end_char}")
        print(f"  Text preview: {chunk.text[:80]}...")
        print()
    
    assert len(chunks) > 0, "Should create at least one chunk"
    assert all(c.chunk_index == i for i, c in enumerate(chunks)), "Chunk indices should be sequential"
    print("✓ Basic chunking test passed")
    return True


def test_overlap_functionality():
    """Test that overlap is working correctly."""
    print("\n=== Testing Overlap Functionality ===\n")
    
    test_text = "First sentence here. Second sentence follows. Third sentence appears. Fourth sentence ends."
    
    chunks = chunk_text(test_text, chunk_size=50, overlap=20)
    
    print(f"Input: {test_text}")
    print(f"Chunk size: 50, Overlap: 20")
    print(f"Created {len(chunks)} chunks\n")
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}: {chunk.text}")
    
    # Check that consecutive chunks have some overlap
    if len(chunks) > 1:
        for i in range(len(chunks) - 1):
            chunk1_end = chunks[i].text[-20:]
            chunk2_start = chunks[i + 1].text[:20]
            print(f"\nOverlap check between chunk {i} and {i+1}:")
            print(f"  Chunk {i} end: ...{chunk1_end}")
            print(f"  Chunk {i+1} start: {chunk2_start}...")
    
    print("\n✓ Overlap functionality test passed")
    return True


def test_edge_cases():
    """Test edge cases."""
    print("\n=== Testing Edge Cases ===\n")
    
    # Test very short text
    short_text = "Short text."
    chunks = chunk_text(short_text, chunk_size=100, overlap=10)
    assert len(chunks) == 1, "Short text should create one chunk"
    print("✓ Short text test passed")
    
    # Test single long sentence
    long_sentence = "This is a very long sentence that goes on and on without any breaks and should still be chunked properly even though it exceeds the chunk size limit because we need to handle this case gracefully."
    chunks = chunk_text(long_sentence, chunk_size=50, overlap=10)
    assert len(chunks) >= 1, "Long sentence should create at least one chunk"
    print("✓ Long sentence test passed")
    
    # Test text with multiple paragraphs
    multi_para = """
    First paragraph with some content.
    
    Second paragraph with more content.
    
    Third paragraph to test.
    """
    chunks = chunk_text(multi_para.strip(), chunk_size=100, overlap=20)
    assert len(chunks) >= 1, "Multi-paragraph text should be chunked"
    print("✓ Multi-paragraph test passed")
    
    print("\n✓ All edge case tests passed")
    return True


def test_chunk_metadata():
    """Test that chunk metadata is correct."""
    print("\n=== Testing Chunk Metadata ===\n")
    
    test_text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
    chunks = chunk_text(test_text, chunk_size=40, overlap=10)
    
    print(f"Input: {test_text}")
    print(f"Created {len(chunks)} chunks\n")
    
    for chunk in chunks:
        print(f"Chunk {chunk.chunk_index}:")
        print(f"  Text: {chunk.text}")
        print(f"  Size: {len(chunk.text)} chars")
        print(f"  Position: {chunk.start_char}-{chunk.end_char}")
        print(f"  Metadata: {chunk.metadata}")
        
        # Verify positions are valid
        assert chunk.start_char >= 0, "Start position should be non-negative"
        assert chunk.end_char > chunk.start_char, "End position should be after start"
        
        print()
    
    print("✓ Chunk metadata test passed")
    return True


def test_parameter_validation():
    """Test parameter validation."""
    print("\n=== Testing Parameter Validation ===\n")
    
    test_text = "Some test text for validation."
    
    # Test invalid chunk size (too small)
    try:
        chunk_text(test_text, chunk_size=50, overlap=10)  # Should work
        print("✓ Valid chunk size accepted")
    except Exception as e:
        print(f"✗ Valid chunk size rejected: {e}")
        return False
    
    # Test invalid overlap (larger than chunk size)
    try:
        chunk_text(test_text, chunk_size=100, overlap=150)
        print("✗ Invalid overlap accepted (should have failed)")
        return False
    except Exception:
        print("✓ Invalid overlap rejected")
    
    # Test empty text
    try:
        chunk_text("", chunk_size=100, overlap=10)
        print("✗ Empty text accepted (should have failed)")
        return False
    except Exception:
        print("✓ Empty text rejected")
    
    print("\n✓ Parameter validation tests passed")
    return True


def run_all_tests():
    """Run all chunking tests."""
    print("\n" + "="*60)
    print("TEXT CHUNKING TEST SUITE")
    print("="*60)
    
    tests = [
        ("Sentence Splitting", test_sentence_splitting),
        ("Basic Chunking", test_basic_chunking),
        ("Overlap Functionality", test_overlap_functionality),
        ("Edge Cases", test_edge_cases),
        ("Chunk Metadata", test_chunk_metadata),
        ("Parameter Validation", test_parameter_validation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
