# /department_of_market_intelligence/tools/tool_config.py
"""
Tool configuration management utilities for Desktop Commander MCP server.
"""

import json
import os
import sys
from typing import Dict, Any

# Add parent directory for imports when run as standalone
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .. import config
except ImportError:
    # Fallback for when running standalone
    import config


def get_desktop_commander_config() -> Dict[str, Any]:
    """Get complete Desktop Commander configuration.
    
    Returns:
        Dictionary containing all Desktop Commander configuration settings
    """
    try:
        from .real_desktop_commander import get_desktop_commander_config as get_real_config
        return get_real_config()
        
    except ImportError:
        print("⚠️  Real configuration interface not available")
    except Exception as e:
        print(f"⚠️  Failed to get real configuration: {e}")
    
    # Fallback configuration
    return {
        "fileWriteLineLimit": 2000,  # Current optimized value
        "fileReadLineLimit": 7000,   # Current optimized value
        "blockedCommands": [],
        "defaultShell": "bash",
        "allowedDirectories": [],
        "telemetryEnabled": True,
        "currentClient": "department_of_market_intelligence",
        "version": "latest"
    }


def set_desktop_commander_config(key: str, value: Any) -> bool:
    """Set a Desktop Commander configuration value.
    
    Args:
        key: Configuration key to set
        value: Value to set
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from .real_desktop_commander import set_desktop_commander_config as set_real_config
        return set_real_config(key, value)
        
    except ImportError:
        print("⚠️  Real configuration interface not available")
        print(f"💡 Use Claude Code MCP tool: mcp__desktop-commander__set_config_value {key} {value}")
        return False
    except Exception as e:
        print(f"⚠️  Failed to set configuration: {e}")
        return False


def set_write_limit(lines: int) -> bool:
    """Set fileWriteLineLimit to specified number of lines.
    
    Args:
        lines: Maximum lines per write_file operation
        
    Returns:
        True if successful, False otherwise
    """
    if lines < 1:
        print("⚠️  Write limit must be at least 1 line")
        return False
        
    return set_desktop_commander_config("fileWriteLineLimit", lines)


def set_read_limit(lines: int) -> bool:
    """Set fileReadLineLimit to specified number of lines.
    
    Args:
        lines: Maximum lines per read_file operation
        
    Returns:
        True if successful, False otherwise
    """
    if lines < 1:
        print("⚠️  Read limit must be at least 1 line")
        return False
        
    return set_desktop_commander_config("fileReadLineLimit", lines)


def show_current_limits() -> None:
    """Display current read/write limits in readable format."""
    try:
        from .real_desktop_commander import show_current_config
        show_current_config()
        
    except ImportError:
        config_data = get_desktop_commander_config()
        
        if not config_data:
            print("❌ Could not retrieve Desktop Commander configuration")
            return
        
        write_limit = config_data.get("fileWriteLineLimit", "unknown")
        read_limit = config_data.get("fileReadLineLimit", "unknown")
        
        print("\n📊 DESKTOP COMMANDER CONFIGURATION")
        print("="*50)
        print(f"📝 Write Limit: {write_limit} lines per operation")
        print(f"📖 Read Limit:  {read_limit} lines per operation")
        print(f"🐚 Default Shell: {config_data.get('defaultShell', 'unknown')}")
        print(f"📁 Allowed Dirs: {'Full access' if not config_data.get('allowedDirectories') else len(config_data.get('allowedDirectories', []))} directories")
        print(f"🚫 Blocked Cmds: {len(config_data.get('blockedCommands', []))} commands")
        print("="*50)


def show_full_config() -> None:
    """Display complete Desktop Commander configuration."""
    config_data = get_desktop_commander_config()
    
    if not config_data:
        print("❌ Could not retrieve Desktop Commander configuration")
        return
    
    print("\n🔧 COMPLETE DESKTOP COMMANDER CONFIGURATION")
    print("="*60)
    print(json.dumps(config_data, indent=2, sort_keys=True))
    print("="*60)


def apply_high_throughput_config() -> bool:
    """Apply configuration optimized for large file operations.
    
    Sets:
    - fileWriteLineLimit: 2000 lines
    - fileReadLineLimit: 7000 lines (increased from 5000)
    
    Returns:
        True if all settings applied successfully
    """
    print("🚀 Applying high-throughput configuration...")
    
    success = True
    success &= set_write_limit(2000)
    success &= set_read_limit(7000)
    
    if success:
        print("✅ High-throughput configuration applied successfully")
        show_current_limits()
    else:
        print("❌ Failed to apply some high-throughput settings")
    
    return success


def apply_conservative_config() -> bool:
    """Apply conservative configuration for stability.
    
    Sets:
    - fileWriteLineLimit: 100 lines
    - fileReadLineLimit: 1000 lines
    
    Returns:
        True if all settings applied successfully
    """
    print("🛡️  Applying conservative configuration...")
    
    success = True
    success &= set_write_limit(100)
    success &= set_read_limit(1000)
    
    if success:
        print("✅ Conservative configuration applied successfully")
        show_current_limits()
    else:
        print("❌ Failed to apply some conservative settings")
    
    return success


def reset_to_defaults() -> bool:
    """Reset Desktop Commander to default configuration.
    
    Sets:
    - fileWriteLineLimit: 50 lines (default)
    - fileReadLineLimit: 1000 lines (default)
    
    Returns:
        True if all settings applied successfully
    """
    print("🔄 Resetting to default configuration...")
    
    success = True
    success &= set_write_limit(50)
    success &= set_read_limit(1000)
    
    if success:
        print("✅ Default configuration restored successfully")
        show_current_limits()
    else:
        print("❌ Failed to reset some settings")
    
    return success


# Configuration presets
PRESETS = {
    "high_throughput": {
        "description": "Optimized for large file operations (DoMI research)",
        "fileWriteLineLimit": 2000,
        "fileReadLineLimit": 7000,
        "apply": apply_high_throughput_config
    },
    "conservative": {
        "description": "Conservative limits for stability", 
        "fileWriteLineLimit": 100,
        "fileReadLineLimit": 1000,
        "apply": apply_conservative_config
    },
    "default": {
        "description": "Desktop Commander default settings",
        "fileWriteLineLimit": 50,
        "fileReadLineLimit": 1000,
        "apply": reset_to_defaults
    }
}


def list_presets() -> None:
    """List available configuration presets."""
    print("\n⚙️  AVAILABLE CONFIGURATION PRESETS")
    print("="*50)
    
    for name, preset in PRESETS.items():
        print(f"📋 {name}:")
        print(f"   {preset['description']}")
        print(f"   Write: {preset['fileWriteLineLimit']} lines")
        print(f"   Read:  {preset['fileReadLineLimit']} lines")
        print()


def apply_preset(preset_name: str) -> bool:
    """Apply a configuration preset by name.
    
    Args:
        preset_name: Name of preset to apply
        
    Returns:
        True if preset applied successfully
    """
    if preset_name not in PRESETS:
        print(f"❌ Unknown preset: {preset_name}")
        print("Available presets:")
        list_presets()
        return False
    
    preset = PRESETS[preset_name]
    print(f"🎯 Applying preset: {preset_name}")
    print(f"   {preset['description']}")
    
    return preset["apply"]()


if __name__ == "__main__":
    # CLI interface when run directly
    import sys
    
    if len(sys.argv) < 2:
        print("📊 Desktop Commander Configuration Manager")
        print("")
        print("🔧 PERSISTENT CONFIGURATION:")
        print("   All configuration changes are PERSISTENT and survive sessions")
        print("")
        print("Usage:")
        print("  python -m tools.tool_config show          - Show current limits")
        print("  python -m tools.tool_config full          - Show full config")
        print("  python -m tools.tool_config presets       - List presets")
        print("  python -m tools.tool_config preset <name> - Apply preset")
        print("  python -m tools.tool_config write <lines> - Set write limit")
        print("  python -m tools.tool_config read <lines>  - Set read limit")
        print("")
        print("🎯 Quick Setup:")
        print("  python -m tools.tool_config preset high_throughput  # For DoMI research")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "show":
        show_current_limits()
    elif command == "full":
        show_full_config()
    elif command == "presets":
        list_presets()
    elif command == "preset" and len(sys.argv) > 2:
        apply_preset(sys.argv[2])
    elif command == "write" and len(sys.argv) > 2:
        try:
            lines = int(sys.argv[2])
            set_write_limit(lines)
        except ValueError:
            print("❌ Invalid number of lines")
    elif command == "read" and len(sys.argv) > 2:
        try:
            lines = int(sys.argv[2])
            set_read_limit(lines)
        except ValueError:
            print("❌ Invalid number of lines")
    else:
        print(f"❌ Unknown command: {command}")