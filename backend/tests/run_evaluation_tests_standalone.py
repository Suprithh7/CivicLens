
import unittest
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

class TestEvaluationService(unittest.TestCase):
    
    def test_relevance_score(self):
        print("\nTesting Relevance Score...")
        # Use more realistic content that will trigger keyword matches
        query = "What are the income requirements for the housing program?"
        answer = "The income requirements state that applicants must earn below 50% of the area median income to be eligible for the housing program."
        score = calculate_relevance_score(query, answer)
        print(f"Relevance Score: {score}")
        self.assertGreater(score, 0.5)
        print("✓ Relevance score test passed")

    def test_coherence_score(self):
        print("\nTesting Coherence Score...")
        score = calculate_coherence_score("This is a coherent sentence.")
        self.assertGreater(score, 0.8)
        print("✓ Coherence score test passed")

    def test_completeness_score(self):
        print("\nTesting Completeness Score...")
        score = calculate_completeness_score("Detailed answer with specific points.", "query")
        self.assertGreater(score, 0.5)
        print("✓ Completeness score test passed")

    def test_source_grounding(self):
        print("\nTesting Source Grounding...")
        sources = [{"chunk_text": "limit is 50k", "policy_title": "Test"}]
        score, flags = check_source_grounding("limit is 50k", sources)
        self.assertGreater(score, 0.0)
        print("✓ Source grounding test passed")

    def test_hallucination_risk(self):
        print("\nTesting Hallucination Risk...")
        risk = detect_hallucination_risk("I think maybe...", [])
        self.assertIn(risk, ["medium", "high"])
        print("✓ Hallucination risk test passed")

    def test_safety_check(self):
        print("\nTesting Safety Check...")
        score, flags = check_safety("Safe content")
        self.assertEqual(score, 1.0)
        self.assertEqual(len(flags), 0)
        print("✓ Safety check test passed")

    def test_evaluate_output(self):
        print("\nTesting Full Evaluation...")
        result = evaluate_output("Answer", "Query", [])
        self.assertIn("overall_confidence", result)
        print("✓ Full evaluation test passed")

if __name__ == '__main__':
    unittest.main()
