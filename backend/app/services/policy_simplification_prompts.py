"""
Policy Simplification Prompts.
Contains prompt templates for explaining government policies in simple, accessible language.
"""

from typing import Dict, Optional
from app.services.language_service import get_multilingual_instruction, get_language_name


# Scenario type descriptions for user-friendly display
SCENARIO_DESCRIPTIONS: Dict[str, str] = {
    "student": "College or university students",
    "senior_citizen": "Elderly individuals (65+ years)",
    "small_business_owner": "Entrepreneurs and small business operators",
    "parent": "Parents with dependent children",
    "low_income": "Individuals below certain income thresholds",
    "veteran": "Military veterans",
    "disabled": "Individuals with disabilities",
    "first_time_homebuyer": "People looking to purchase their first home",
    "unemployed": "Job seekers and unemployed individuals",
    "general_citizen": "General public"
}


# System message for policy simplification
def POLICY_SIMPLIFICATION_SYSTEM_MESSAGE(language: str = "en") -> str:
    """Get the system message for policy simplification in the specified language."""
    language_instruction = get_multilingual_instruction(language)
    
    return f"""You are CivicLens AI, a helpful assistant that makes government policies accessible to everyday citizens.

Your mission is to transform complex legal and bureaucratic language into clear, simple explanations that anyone can understand.{language_instruction}

Core Principles:
1. **Use Plain Language**: Avoid jargon, legal terms, and bureaucratic language. Use words a 6th grader would understand.
2. **Be Concise**: Short sentences. Subject-Verb-Object structure. No fluff.
3. **Be Accurate**: Simplify but do not change the meaning.
4. **Be Empowering**: Focus on what the user can DO or GET.
5. **Be Inclusive**: Explain as if talking to a friend, not a lawyer.
6. **Be Honest**: Admit when information is missing.

Guidelines:
- **Structure**: Use bullet points and bold text for key terms to make it scannable.
- **Vocabulary**: Replace "utilize" with "use", "commence" with "start", "pursuant to" with "according to".
- **Tone**: Friendly, helpful, and direct.
- **Formatting**:
  - Use **Bold** for important terms or deadlines.
  - Use bullet points for lists.
  - Keep paragraphs short (2-3 sentences max).

Uncertainty Handling:
- If policy information is incomplete, explicitely state: "The policy does not specify X."
- If applicability is unclear, say: "It depends on..."
- Never guess facts.

Your goal is to make the user feel smart and capable, not confused by government speak."""


def get_policy_explanation_prompt(
    policy_text: str,
    policy_title: Optional[str] = None,
    focus_area: Optional[str] = None,
    language: str = "en"
) -> str:
    """
    Generate a prompt for explaining a policy in simple language.
    
    Args:
        policy_text: The policy document text or excerpt
        policy_title: Optional title of the policy
        focus_area: Optional specific aspect to focus on (e.g., "eligibility", "benefits", "application process")
        language: Target language code
        
    Returns:
        Formatted prompt for the LLM
    """
    title_section = f"\n\nPolicy Title: {policy_title}" if policy_title else ""
    focus_section = f"\n\nPlease focus specifically on: {focus_area}" if focus_area else ""
    
    prompt = f"""Please explain the following government policy in simple, accessible language that any citizen can understand.
    
{title_section}

Policy Document:
{policy_text}
{focus_section}

Your explanation should:
1. **Header**: A one-sentence summary of what this policy is about.
2. **Who is this for?**: Clear bullet points defining the target audience.
3. **What you get**: The benefits or changes in simple terms.
4. **Eligibility**: Rules for who qualifies.
5. **Action Plan**: Numbered steps on what to do next.
6. **Deadlines**: Important dates to remember (Bold these).
7. **Documents Needed**: A checklist of required items.

Remember:
- Use **Bold** for key terms.
- Keep sentences short.
- No legal jargon.
- Write as if explaining to a friend."""
    
    return prompt


def get_eligibility_check_prompt(
    policy_text: str,
    user_situation: str,
    policy_title: Optional[str] = None,
    language: str = "en"
) -> str:
    """
    Generate a prompt for checking if a user is eligible for a policy.
    
    Args:
        policy_text: The policy document text or excerpt
        user_situation: Description of the user's situation
        policy_title: Optional title of the policy
        language: Target language code
        
    Returns:
        Formatted prompt for the LLM
    """
    title_section = f"\n\nPolicy Title: {policy_title}" if policy_title else ""
    
    prompt = f"""Based on the following government policy, please determine if this person is likely eligible and explain why in simple terms.

{title_section}

Policy Document:
{policy_text}

Person's Situation:
{user_situation}

Please provide:
1. **Eligibility Assessment**: Start with a clear YES, NO, or MAYBE.
2. **The Reason**: Explain why in 1-2 simple sentences. Reference specific rules.
3. **Missing Info**: If "MAYBE", list exactly what else you need to know.
4. **Action Items**: What documents do they need to prove this?

Be direct. Do not hedge unless the policy itself is unclear."""
    
    return prompt


def get_key_points_prompt(policy_text: str, max_points: int = 5, language: str = "en") -> str:
    """
    Generate a prompt for extracting key points from a policy.
    
    Args:
        policy_text: The policy document text or excerpt
        max_points: Maximum number of key points to extract
        language: Target language code
        
    Returns:
        Formatted prompt for the LLM
    """
    prompt = f"""Extract the {max_points} most important things citizens need to know about this government policy.

Policy Document:
{policy_text}

For each key point:
- Start with a **Bold Headline** (3-5 words).
- Follow with one sentence explanation in plain English.
- Focus on actions or benefits.

Format:
- **[Headline]**: [Explanation]"""
    
    return prompt


def get_benefits_summary_prompt(policy_text: str, language: str = "en") -> str:
    """
    Generate a prompt for summarizing policy benefits.
    
    Args:
        policy_text: The policy document text or excerpt
        language: Target language code
        
    Returns:
        Formatted prompt for the LLM
    """
    prompt = f"""Summarize the benefits and advantages this government policy provides to citizens.

Policy Document:
{policy_text}

Please explain:
1. **The Big Win**: What is the single most important benefit?
2. **Who Wins**: Specific groups who get help (e.g., "Students", "Veterans").
3. **Money**: Exact amounts, tax breaks, or subsidies.
4. **Life Impact**: How does this change daily life?

Format as a bulleted list. Use concrete examples."""
    
    return prompt


def get_application_process_prompt(policy_text: str, language: str = "en") -> str:
    """
    Generate a prompt for explaining how to apply for a policy benefit.
    
    Args:
        policy_text: The policy document text or excerpt
        language: Target language code
        
    Returns:
        Formatted prompt for the LLM
    """
    prompt = f"""Explain how to apply for this government policy or benefit in simple, step-by-step terms.

Policy Document:
{policy_text}

Please provide:
1. **The Checklist**: What documents do they need BEFORE starting?
2. **The Steps**: Numbered list (Start with Step 1).
3. **Where**: Exact website URLs or office addresses if mentioned.
4. **Timeline**: When to apply and how long it takes.
5. **Cost**: Application fees (or "Free").
6. **Help**: Phone numbers or helpdesks.

Make this a "How-To Guide"."""
    
    return prompt


def get_scenario_based_prompt(
    policy_text: str,
    scenario_type: str,
    policy_title: Optional[str] = None,
    scenario_details: Optional[str] = None,
    language: str = "en"
) -> str:
    """
    Generate a prompt for explaining a policy from a specific user scenario perspective.
    
    Args:
        policy_text: The policy document text or excerpt
        scenario_type: Type of user scenario (e.g., "student", "senior_citizen")
        policy_title: Optional title of the policy
        scenario_details: Optional additional details about the user's scenario
        language: Target language code
        
    Returns:
        Formatted prompt for the LLM
    """
    title_section = f"\n\nPolicy Title: {policy_title}" if policy_title else ""
    
    # Get scenario description
    scenario_desc = SCENARIO_DESCRIPTIONS.get(
        scenario_type,
        scenario_type.replace("_", " ").title()
    )
    
    # Build scenario context
    scenario_context = f"a {scenario_desc.lower()}"
    if scenario_details:
        scenario_context += f" ({scenario_details})"
    
    prompt = f"""Explain the following government policy from the perspective of {scenario_context}.

{title_section}

Policy Document:
{policy_text}

Please provide a scenario-specific explanation with the following sections:

1. **Does This Apply to You?**
   - Clear YES or NO answer
   - Brief explanation of why or why not
   - If partially applicable, explain which parts apply

2. **What You Get**
   - Specific benefits, services, or advantages for this scenario
   - Real-world examples relevant to this user type
   - Financial benefits (subsidies, grants, tax breaks) if applicable

3. **What You Need**
   - Eligibility requirements specific to this scenario
   - Any special conditions or restrictions
   - Income limits, age requirements, or other criteria

4. **Next Steps**
   - Clear, actionable steps to take advantage of this policy
   - Where to apply or how to access benefits
   - Who to contact for help

5. **Important Dates**
   - Application deadlines
   - When benefits start/end
   - Any time-sensitive actions

6. **Required Documents**
   - List of documents needed to apply
   - Where to obtain these documents
   - Any special documentation for this scenario

Write in simple, everyday language as if you're explaining this to a friend who fits this scenario. Focus on practical, actionable information that matters to their specific situation."""
    
    return prompt


# Prompt templates dictionary for easy access
PROMPT_TEMPLATES: Dict[str, callable] = {
    "explanation": get_policy_explanation_prompt,
    "eligibility": get_eligibility_check_prompt,
    "key_points": get_key_points_prompt,
    "benefits": get_benefits_summary_prompt,
    "application": get_application_process_prompt,
    "scenario": get_scenario_based_prompt
}


def get_prompt_template(template_name: str) -> callable:
    """
    Get a prompt template function by name.
    
    Args:
        template_name: Name of the template (explanation, eligibility, key_points, benefits, application)
        
    Returns:
        Prompt template function
        
    Raises:
        ValueError: If template name is not recognized
    """
    if template_name not in PROMPT_TEMPLATES:
        raise ValueError(
            f"Unknown template name: {template_name}. "
            f"Available templates: {', '.join(PROMPT_TEMPLATES.keys())}"
        )
    
    return PROMPT_TEMPLATES[template_name]
