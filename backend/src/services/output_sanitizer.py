"""
Output sanitization - prevent XSS and injection attacks
"""
import html
import re
from typing import Any


def sanitize_html(text: str) -> str:
    """Escape HTML characters to prevent XSS"""
    return html.escape(text)


def sanitize_json_output(data: Any) -> Any:
    """Recursively sanitize JSON output"""
    if isinstance(data, str):
        # Remove potential script tags and dangerous patterns
        data = re.sub(r'<script[^>]*>.*?</script>', '', data, flags=re.IGNORECASE | re.DOTALL)
        data = re.sub(r'javascript:', '', data, flags=re.IGNORECASE)
        data = re.sub(r'on\w+\s*=', '', data, flags=re.IGNORECASE)
        return sanitize_html(data)
    elif isinstance(data, dict):
        return {k: sanitize_json_output(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_output(item) for item in data]
    else:
        return data


def sanitize_llm_output(content: str) -> str:
    """Sanitize LLM output for safe rendering"""
    # Remove HTML tags (we'll render as plain text)
    content = re.sub(r'<[^>]+>', '', content)
    # Escape remaining HTML entities
    content = sanitize_html(content)
    # Remove dangerous patterns
    content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
    content = re.sub(r'on\w+\s*=', '', content, flags=re.IGNORECASE)
    return content

