#!/usr/bin/env python3
"""Test Security Freeze v1 - verify hard mode and retention."""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def test_source_safety_mode_hard_mode():
    """Test that SOURCE_SAFETY_MODE is forced in production."""
    print("Testing SOURCE_SAFETY_MODE hard mode...")
    
    # Set DEBUG=false and SOURCE_SAFETY_MODE=false
    os.environ["DEBUG"] = "false"
    os.environ["SOURCE_SAFETY_MODE"] = "false"
    
    # Clear any cached settings
    if "app.core.config" in sys.modules:
        del sys.modules["app.core.config"]
    
    try:
        from app.core.config import settings
        print("❌ Should have raised ValueError")
        return False
    except ValueError as e:
        if "SOURCE_SAFETY_MODE cannot be False" in str(e):
            print("✅ Boot correctly fails when SOURCE_SAFETY_MODE=false in prod")
            return True
        else:
            print(f"❌ Wrong error: {e}")
            return False
    finally:
        # Cleanup
        if "DEBUG" in os.environ:
            del os.environ["DEBUG"]
        if "SOURCE_SAFETY_MODE" in os.environ:
            del os.environ["SOURCE_SAFETY_MODE"]


def test_source_safety_mode_forced_true():
    """Test that SOURCE_SAFETY_MODE is forced to True in production."""
    print("Testing SOURCE_SAFETY_MODE forced to True...")
    
    # Set DEBUG=false (production)
    os.environ["DEBUG"] = "false"
    # Don't set SOURCE_SAFETY_MODE (should default to True)
    
    # Clear any cached settings
    if "app.core.config" in sys.modules:
        del sys.modules["app.core.config"]
    
    try:
        from app.core.config import settings
        assert settings.debug is False, "DEBUG should be False"
        assert settings.source_safety_mode is True, "SOURCE_SAFETY_MODE should be forced to True"
        print("✅ SOURCE_SAFETY_MODE is forced to True in production")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Cleanup
        if "DEBUG" in os.environ:
            del os.environ["DEBUG"]


def test_retention_settings():
    """Test that retention settings are available."""
    print("Testing retention settings...")
    
    # Clear any cached settings
    if "app.core.config" in sys.modules:
        del sys.modules["app.core.config"]
    
    try:
        from app.core.config import settings
        assert hasattr(settings, "retention_days_default"), "retention_days_default should exist"
        assert hasattr(settings, "retention_days_sensitive"), "retention_days_sensitive should exist"
        assert hasattr(settings, "temp_file_ttl_hours"), "temp_file_ttl_hours should exist"
        assert settings.retention_days_default == 30, "Default retention should be 30 days"
        assert settings.retention_days_sensitive == 7, "Sensitive retention should be 7 days"
        assert settings.temp_file_ttl_hours == 24, "Temp file TTL should be 24 hours"
        print("✅ Retention settings are available and have correct defaults")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SECURITY FREEZE v1 TESTS")
    print("=" * 60)
    print()
    
    tests = [
        test_source_safety_mode_hard_mode,
        test_source_safety_mode_forced_true,
        test_retention_settings,
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

