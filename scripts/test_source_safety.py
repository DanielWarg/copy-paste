#!/usr/bin/env python3
"""Test Source Safety Mode - verify no source identifiers leak."""
import sys
import os
from pathlib import Path

# Set SOURCE_SAFETY_MODE before importing app modules
os.environ["SOURCE_SAFETY_MODE"] = "true"
os.environ["DEBUG"] = "true"  # Enable assertions

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.privacy_guard import sanitize_for_logging, assert_no_content
from app.core.config import settings


def test_source_identifiers_blocked():
    """Test that source identifiers are blocked in logs/audit."""
    print("Testing source identifier blocking...")
    
    # Test data with source identifiers
    test_data = {
        "action": "file_uploaded",
        "ip": "192.168.1.1",  # Should be blocked
        "client_ip": "10.0.0.1",  # Should be blocked
        "user_agent": "Mozilla/5.0",  # Should be blocked
        "referer": "https://example.com",  # Should be blocked
        "filename": "source.pdf",  # Should be blocked
        "original_filename": "källa.pdf",  # Should be blocked
        "url": "https://example.com/file",  # Should be blocked
        "count": 1,  # Should pass
        "transcript_id": 123,  # Should pass
    }
    
    # In DEV mode, sanitize_for_logging should raise AssertionError
    # In PROD mode, it should drop fields silently
    if settings.debug:
        # DEV mode: Should raise AssertionError
        try:
            sanitize_for_logging(test_data, context="test")
            print("❌ Should have raised AssertionError in DEV mode")
            return False
        except AssertionError:
            print("✅ Source identifiers correctly raise AssertionError in DEV mode")
            return True
    else:
        # PROD mode: Should drop fields silently
        sanitized = sanitize_for_logging(test_data, context="test")
        
        # Verify blocked fields are removed
        assert "ip" not in sanitized, "IP should be blocked"
        assert "client_ip" not in sanitized, "client_ip should be blocked"
        assert "user_agent" not in sanitized, "user_agent should be blocked"
        assert "referer" not in sanitized, "referer should be blocked"
        assert "filename" not in sanitized, "filename should be blocked"
        assert "original_filename" not in sanitized, "original_filename should be blocked"
        assert "url" not in sanitized, "url should be blocked"
        
        # Verify allowed fields remain
        assert "action" in sanitized, "action should remain"
        assert "count" in sanitized, "count should remain"
        assert "transcript_id" in sanitized, "transcript_id should remain"
        
        print("✅ Source identifiers correctly blocked in PROD mode")
        return True


def test_content_blocked():
    """Test that content is blocked in logs/audit."""
    print("Testing content blocking...")
    
    test_data = {
        "action": "transcript_created",
        "transcript_text": "Detta är förbjudet innehåll",  # Should be blocked
        "body": "Förbjudet body",  # Should be blocked
        "count": 1,  # Should pass
    }
    
    # In DEV mode, sanitize_for_logging should raise AssertionError
    if settings.debug:
        # DEV mode: Should raise AssertionError
        try:
            sanitize_for_logging(test_data, context="test")
            print("❌ Should have raised AssertionError in DEV mode")
            return False
        except AssertionError:
            print("✅ Content correctly raises AssertionError in DEV mode")
            return True
    else:
        # PROD mode: Should drop fields silently
        sanitized = sanitize_for_logging(test_data, context="test")
        
        assert "transcript_text" not in sanitized, "transcript_text should be blocked"
        assert "body" not in sanitized, "body should be blocked"
        assert "count" in sanitized, "count should remain"
        
        print("✅ Content correctly blocked in PROD mode")
        return True


def test_assert_no_content():
    """Test assert_no_content raises on violations."""
    print("Testing assert_no_content...")
    
    # Should raise
    try:
        assert_no_content({"ip": "192.168.1.1"}, context="test")
        print("❌ assert_no_content should have raised AssertionError")
        return False
    except AssertionError:
        print("✅ assert_no_content correctly raises on violations")
    
    # Should pass
    try:
        assert_no_content({"action": "created", "count": 1}, context="test")
        print("✅ assert_no_content passes on safe data")
        return True
    except AssertionError as e:
        print(f"❌ assert_no_content incorrectly raised: {e}")
        return False


def test_source_safety_mode_toggle():
    """Test that SOURCE_SAFETY_MODE toggle works."""
    print("Testing SOURCE_SAFETY_MODE toggle...")
    
    # Verify SOURCE_SAFETY_MODE is enabled
    assert settings.source_safety_mode is True, "SOURCE_SAFETY_MODE should be True"
    print("✅ SOURCE_SAFETY_MODE is enabled")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("SOURCE SAFETY MODE TESTS")
    print("=" * 60)
    print()
    
    tests = [
        test_source_identifiers_blocked,
        test_content_blocked,
        test_assert_no_content,
        test_source_safety_mode_toggle,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
            print()
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

