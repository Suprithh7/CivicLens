
import sys
import os
import logging

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.services.evaluation_service import evaluate_output

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_evaluation_fix():
    output_file = "verification_results.txt"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Testing Evaluation Fix...\n")
            
            # Mock Data
            policy_text = """
            The Affordable Connectivity Program (ACP) provides a discount of up to $30 per month toward internet service for eligible households. 
            Eligible households can also receive a one-time discount of up to $100 to purchase a laptop, desktop computer, or tablet.
            To be eligible, a household must have an income at or below 200% of the Federal Poverty Guidelines.
            """
            
            simplified_answer = """
            **The Big Win**: You get $30 off your internet bill every month.
            
            **What You Get**:
            - $30 monthly discount on internet.
            - $100 off a new computer or tablet.
            
            **Eligibility**:
            - Your income must be low.
            - Specifically, below 200% of the poverty line.
            
            **Action Plan**:
            1. Check if you qualify.
            2. Apply online.
            """
            
            query = "Explain the Affordable Connectivity Program benefits."
            
            f.write("\nRunning evaluate_output...\n")
            result = evaluate_output(
                answer=simplified_answer,
                query=query,
                sources=[],
                context={"policy_text": policy_text}
            )
            
            f.write("\nEvaluation Results:\n")
            f.write(f"Confidence: {result['overall_confidence']}\n")
            f.write(f"Grounding Score: {result['source_grounding_score']}\n")
            f.write(f"Coherence Score: {result['coherence_score']}\n")
            f.write(f"Completeness Score: {result['completeness_score']}\n")
            f.write(f"Quality Flags: {result['quality_flags']}\n")
            
            failures = []
            
            if result['source_grounding_score'] < 0.5:
                failures.append(f"Grounding score too low ({result['source_grounding_score']}). Should be high because policy_text is provided.")
            else:
                f.write("✅ Grounding Score Check Passed\n")
                
            if result['coherence_score'] < 0.7:
                failures.append(f"Coherence score too low ({result['coherence_score']}). Short sentences should be allowed.")
            else:
                f.write("✅ Coherence Score Check Passed\n")
                
            if "no_sources" in result['quality_flags']:
                failures.append("❌ 'no_sources' flag present. It should not be present when context.policy_text is provided.")
            else:
                f.write("✅ 'no_sources' Flag Check Passed\n")

            f.write(f"\nTest Summary: {'FAILED' if failures else 'PASSED'}\n")
            if failures:
                f.write("Failures:\n")
                for fail in failures:
                    f.write(f"- {fail}\n")
    except Exception as e:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"\nEXCEPTION: {str(e)}\n")
        raise e

if __name__ == "__main__":
    test_evaluation_fix()
