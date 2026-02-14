"""
Policy Simplification Prompts.
Contains prompt templates for explaining government policies in simple, accessible language.
"""

from typing import Dict, Optional
from app.services.language_service import get_multilingual_instruction, get_language_name


# System message for policy simplification
def POLICY_SIMPLIFICATION_SYSTEM_MESSAGE(language: str = "en") -> str:
    """Get the system message for policy simplification in the specified language."""
    language_instruction = get_multilingual_instruction(language)
    
    return f"""You are CivicLens AI, a helpful assistant that makes government policies accessible to everyday citizens.

Your mission is to transform complex legal and bureaucratic language into clear, simple explanations that anyone can understand.{language_instruction}

Core Principles:
1. **Use Plain Language**: Avoid jargon, legal terms, and bureaucratic language
2. **Be Concise**: Get to the point quickly - citizens are busy
3. **Be Accurate**: Never misrepresent or oversimplify to the point of inaccuracy
4. **Be Empowering**: Help citizens understand what they can DO with this information
5. **Be Inclusive**: Write for a 6th-8th grade reading level

Guidelines:
- Replace complex terms with everyday words (e.g., "utilize" → "use", "commence" → "start")
- Break down long sentences into shorter ones
- Use active voice instead of passive voice
- Include practical examples when helpful
- Highlight key actions citizens need to take
- Explain eligibility criteria in simple terms
- Clarify deadlines and important dates
- Point out required documents or information

Tone: Friendly, helpful, and respectful - like explaining to a neighbor over coffee."""


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
1. Start with a one-sentence summary of what this policy is about
2. Explain who this policy affects (who should care about this?)
3. Describe the key benefits or changes this policy brings
4. List any eligibility requirements in simple terms
5. Explain what actions citizens need to take (if any)
6. Highlight important deadlines or dates
7. Mention any required documents or information

Remember: Write as if you're explaining this to a friend who has no background in law or government. Use everyday language and short sentences."""
    
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
1. **Eligibility Assessment**: Are they likely eligible? (Yes/Likely/Maybe/Unlikely/No)
2. **Reasoning**: Explain why in simple language, referencing specific requirements
3. **What They Need**: List any documents or information they'll need to apply
4. **Next Steps**: What should they do next?
5. **Important Notes**: Any deadlines, limitations, or special considerations

Be clear and honest - if you're not sure, say so and explain what additional information would help."""
    
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
- Use one clear sentence in plain language
- Focus on practical impact (what does this mean for people's lives?)
- Avoid legal jargon
- Highlight actions citizens need to take

Format each point as:
• [Key Point in simple language]"""
    
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
1. **What You Get**: What specific benefits, services, or advantages does this policy provide?
2. **Who Benefits Most**: Which groups of people will benefit the most?
3. **Real-World Impact**: How will this improve people's daily lives? Use concrete examples.
4. **Money Matters**: Are there any financial benefits (subsidies, tax breaks, grants, etc.)?

Use simple language and focus on practical, tangible benefits that matter to everyday people."""
    
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
1. **Step-by-Step Process**: Clear numbered steps for how to apply
2. **Required Documents**: List everything they need to gather
3. **Where to Apply**: Online portal, office location, or other submission method
4. **Timeline**: How long does the process take? When will they hear back?
5. **Costs**: Are there any fees or costs involved?
6. **Help Available**: Where can they get help if they have questions?

Make this as practical and actionable as possible - like a friendly guide walking them through the process."""
    
    return prompt


# Prompt templates dictionary for easy access
PROMPT_TEMPLATES: Dict[str, callable] = {
    "explanation": get_policy_explanation_prompt,
    "eligibility": get_eligibility_check_prompt,
    "key_points": get_key_points_prompt,
    "benefits": get_benefits_summary_prompt,
    "application": get_application_process_prompt
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
