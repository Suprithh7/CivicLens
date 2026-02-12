"""
Example usage of policy simplification prompts.
Demonstrates how to use the prompt templates with the LLM service.
"""

from app.services.policy_simplification_prompts import (
    POLICY_SIMPLIFICATION_SYSTEM_MESSAGE,
    get_policy_explanation_prompt,
    get_eligibility_check_prompt,
    get_key_points_prompt,
    get_benefits_summary_prompt,
    get_application_process_prompt
)
from app.services.llm_service import generate_completion


# Example policy text (sample healthcare policy)
SAMPLE_POLICY = """
Section 4.2: Healthcare Subsidy Eligibility Criteria

Pursuant to the Healthcare Accessibility Act of 2024, eligible beneficiaries 
shall be entitled to receive subsidized healthcare coverage as follows:

(a) Income Requirements: Applicants whose annual household income does not 
exceed 250% of the Federal Poverty Level (FPL) shall be deemed eligible for 
full subsidy coverage. Applicants with household income between 250% and 400% 
of FPL may qualify for partial subsidy on a sliding scale basis.

(b) Residency Requirements: Applicants must provide documentation demonstrating 
continuous residency within the jurisdiction for a minimum period of twelve (12) 
consecutive months immediately preceding the date of application.

(c) Documentation: Applicants shall submit the following documentation:
    (i) Proof of income (tax returns, pay stubs, or equivalent documentation)
    (ii) Government-issued photo identification
    (iii) Proof of residency (utility bills, lease agreements, or equivalent)
    (iv) Social Security numbers for all household members

(d) Application Process: Applications must be submitted electronically via the 
state healthcare portal (www.statehealthcare.gov) or in person at designated 
enrollment centers. The enrollment period commences on November 1st and 
concludes on January 31st of each calendar year.

(e) Processing Timeline: Applications shall be processed within forty-five (45) 
business days of receipt. Applicants will be notified of eligibility determination 
via postal mail and electronic communication.
"""


async def example_basic_explanation():
    """Example: Get a simple explanation of a policy."""
    
    # Generate the prompt
    prompt = get_policy_explanation_prompt(
        policy_text=SAMPLE_POLICY,
        policy_title="Healthcare Subsidy Program 2024"
    )
    
    # Get explanation from LLM
    explanation = await generate_completion(
        prompt=prompt,
        system_message=POLICY_SIMPLIFICATION_SYSTEM_MESSAGE,
        temperature=0.7
    )
    
    print("=== POLICY EXPLANATION ===")
    print(explanation)
    print("\n")
    
    return explanation


async def example_eligibility_check():
    """Example: Check if someone is eligible for a policy."""
    
    user_situation = """
    I'm a single parent living in the state for 2 years. I work part-time and 
    make about $35,000 a year. I have two kids. I have my tax returns and 
    driver's license.
    """
    
    # Generate the prompt
    prompt = get_eligibility_check_prompt(
        policy_text=SAMPLE_POLICY,
        user_situation=user_situation,
        policy_title="Healthcare Subsidy Program 2024"
    )
    
    # Get eligibility assessment from LLM
    assessment = await generate_completion(
        prompt=prompt,
        system_message=POLICY_SIMPLIFICATION_SYSTEM_MESSAGE,
        temperature=0.3  # Lower temperature for more factual responses
    )
    
    print("=== ELIGIBILITY ASSESSMENT ===")
    print(assessment)
    print("\n")
    
    return assessment


async def example_key_points():
    """Example: Extract key points from a policy."""
    
    # Generate the prompt
    prompt = get_key_points_prompt(
        policy_text=SAMPLE_POLICY,
        max_points=5
    )
    
    # Get key points from LLM
    key_points = await generate_completion(
        prompt=prompt,
        system_message=POLICY_SIMPLIFICATION_SYSTEM_MESSAGE,
        temperature=0.5
    )
    
    print("=== KEY POINTS ===")
    print(key_points)
    print("\n")
    
    return key_points


async def example_benefits_summary():
    """Example: Summarize policy benefits."""
    
    # Generate the prompt
    prompt = get_benefits_summary_prompt(policy_text=SAMPLE_POLICY)
    
    # Get benefits summary from LLM
    benefits = await generate_completion(
        prompt=prompt,
        system_message=POLICY_SIMPLIFICATION_SYSTEM_MESSAGE,
        temperature=0.6
    )
    
    print("=== BENEFITS SUMMARY ===")
    print(benefits)
    print("\n")
    
    return benefits


async def example_application_process():
    """Example: Explain how to apply."""
    
    # Generate the prompt
    prompt = get_application_process_prompt(policy_text=SAMPLE_POLICY)
    
    # Get application guide from LLM
    guide = await generate_completion(
        prompt=prompt,
        system_message=POLICY_SIMPLIFICATION_SYSTEM_MESSAGE,
        temperature=0.5
    )
    
    print("=== APPLICATION PROCESS ===")
    print(guide)
    print("\n")
    
    return guide


async def run_all_examples():
    """Run all example prompts."""
    
    print("=" * 60)
    print("POLICY SIMPLIFICATION EXAMPLES")
    print("=" * 60)
    print("\n")
    
    await example_basic_explanation()
    await example_eligibility_check()
    await example_key_points()
    await example_benefits_summary()
    await example_application_process()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_all_examples())
