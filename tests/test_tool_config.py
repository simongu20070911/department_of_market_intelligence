#!/usr/bin/env python3
# /department_of_market_intelligence/tests/test_tool_config.py
"""
Test suite for Desktop Commander tool configuration management.
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_config import (
    get_desktop_commander_config,
    set_write_limit,
    set_read_limit,
    show_current_limits,
    apply_preset,
    PRESETS
)


class TestToolConfig(unittest.TestCase):
    """Test Desktop Commander configuration management."""
    
    def test_get_config(self):
        """Test getting Desktop Commander configuration."""
        config = get_desktop_commander_config()
        self.assertIsInstance(config, dict)
        self.assertIn("fileWriteLineLimit", config)
        self.assertIn("fileReadLineLimit", config)
    
    def test_presets_available(self):
        """Test that configuration presets are available."""
        self.assertIn("high_throughput", PRESETS)
        self.assertIn("conservative", PRESETS)
        self.assertIn("default", PRESETS)
        
        for preset_name, preset in PRESETS.items():
            self.assertIn("description", preset)
            self.assertIn("fileWriteLineLimit", preset)
            self.assertIn("fileReadLineLimit", preset)
            self.assertIn("apply", preset)
    
    def test_set_limits_validation(self):
        """Test that limit setting functions validate input."""
        # Test invalid limits
        result = set_write_limit(0)
        self.assertFalse(result)
        
        result = set_read_limit(-1)
        self.assertFalse(result)
        
        # Test valid limits (these will succeed in mock mode)
        result = set_write_limit(100)
        self.assertTrue(result)
        
        result = set_read_limit(1000)
        self.assertTrue(result)
    
    def test_preset_application(self):
        """Test applying configuration presets."""
        # Test valid presets
        for preset_name in PRESETS.keys():
            result = apply_preset(preset_name)
            self.assertTrue(result, f"Failed to apply preset: {preset_name}")
        
        # Test invalid preset
        result = apply_preset("nonexistent_preset")
        self.assertFalse(result)
    
    def test_show_limits_no_crash(self):
        """Test that show_current_limits doesn't crash."""
        try:
            show_current_limits()
        except Exception as e:
            self.fail(f"show_current_limits raised an exception: {e}")


class TestConfigIntegration(unittest.TestCase):
    """Test integration with main config module."""
    
    def test_config_functions_available(self):
        """Test that config integration functions are available."""
        from department_of_market_intelligence import config
        
        # Check that integration functions exist
        self.assertTrue(hasattr(config, 'log_tool_configuration'))
        self.assertTrue(hasattr(config, 'apply_auto_optimization'))
        self.assertTrue(hasattr(config, 'validate_tool_configuration'))
    
    def test_config_validation(self):
        """Test config validation function."""
        from department_of_market_intelligence.config import validate_tool_configuration
        
        # This should not crash
        try:
            result = validate_tool_configuration()
            self.assertIsInstance(result, bool)
        except Exception as e:
            self.fail(f"validate_tool_configuration raised an exception: {e}")


def run_integration_test():
    """Run a comprehensive integration test."""
    print("🧪 RUNNING DESKTOP COMMANDER CONFIGURATION TESTS")
    print("="*60)
    
    # Test 1: Basic functionality
    print("1. Testing basic configuration retrieval...")
    config = get_desktop_commander_config()
    if config:
        print("   ✅ Configuration retrieved successfully")
        print(f"   📝 Write Limit: {config.get('fileWriteLineLimit', 'unknown')}")
        print(f"   📖 Read Limit: {config.get('fileReadLineLimit', 'unknown')}")
    else:
        print("   ❌ Failed to retrieve configuration")
    
    # Test 2: Preset functionality
    print("\n2. Testing configuration presets...")
    print(f"   📋 Available presets: {list(PRESETS.keys())}")
    
    # Test 3: Limits display
    print("\n3. Testing limits display...")
    show_current_limits()
    
    # Test 4: Integration with main config
    print("\n4. Testing main config integration...")
    try:
        from department_of_market_intelligence.config import validate_tool_configuration
        result = validate_tool_configuration()
        print(f"   ✅ Config validation result: {result}")
    except Exception as e:
        print(f"   ❌ Config integration error: {e}")
    
    print("\n✅ Integration tests completed")


if __name__ == "__main__":
    # Check if running integration test
    if len(sys.argv) > 1 and sys.argv[1] == "integration":
        run_integration_test()
    else:
        # Run unit tests
        unittest.main()