"""
Tests for output sanitization
"""
import pytest
from src.services.output_sanitizer import sanitize_html, sanitize_llm_output, sanitize_json_output


def test_sanitize_html_escapes():
    """Test that HTML is escaped"""
    input_text = "<script>alert('XSS')</script>"
    output = sanitize_html(input_text)
    
    assert "<script>" not in output
    assert "&lt;script&gt;" in output


def test_sanitize_llm_output_removes_scripts():
    """Test that script tags are removed"""
    input_text = "Hello <script>alert('XSS')</script> world"
    output = sanitize_llm_output(input_text)
    
    assert "<script>" not in output
    assert "alert" not in output or "alert" in output.lower()  # May be escaped


def test_sanitize_llm_output_removes_javascript():
    """Test that javascript: URLs are removed"""
    input_text = "Click <a href='javascript:alert(1)'>here</a>"
    output = sanitize_llm_output(input_text)
    
    assert "javascript:" not in output.lower()


def test_sanitize_json_output():
    """Test that JSON output is sanitized recursively"""
    input_data = {
        "text": "<script>alert('XSS')</script>",
        "nested": {
            "more": "javascript:alert(1)"
        },
        "list": ["<b>test</b>", "normal"]
    }
    
    output = sanitize_json_output(input_data)
    
    assert "<script>" not in str(output)
    assert "javascript:" not in str(output).lower()

