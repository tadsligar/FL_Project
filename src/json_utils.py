"""
Utility functions for JSON parsing from LLM responses.
"""

import json
import re


def extract_json_from_llm_response(text: str) -> dict:
    """
    Extract JSON from LLM response, handling various formats.

    Handles:
    - Markdown code blocks (```json or ```)
    - Preamble text ("Here is the output:", etc.)
    - Trailing text after JSON
    - JSON comments (// and /* */)

    Args:
        text: Raw LLM response

    Returns:
        Parsed JSON dict

    Raises:
        json.JSONDecodeError: If no valid JSON found
    """
    text = text.strip()

    # Remove markdown code blocks if present
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    # Find the first '{' - this is where the JSON actually starts
    # (handles cases like "Here is the output:\n\n{...}")
    json_start = text.find('{')
    if json_start > 0:
        text = text[json_start:]
    elif json_start < 0:
        # No JSON found - try to find array start
        json_start = text.find('[')
        if json_start > 0:
            text = text[json_start:]

    # Find the last '}' or ']' - this is where the JSON ends
    json_end = max(text.rfind('}'), text.rfind(']'))
    if json_end > 0:
        text = text[:json_end + 1]

    # Remove JSON comments that LLM may add
    # Remove single-line comments (// ...)
    text = re.sub(r'//[^\n]*', '', text)

    # Remove multi-line comments (/* ... */)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    return json.loads(text)
