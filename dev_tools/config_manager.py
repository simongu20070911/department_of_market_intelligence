#!/usr/bin/env python3
# /department_of_market_intelligence/dev_tools/config_manager.py
"""
Command-line interface for managing Desktop Commander MCP server configuration.
"""

import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.tool_config import (
    show_current_limits,
    show_full_config,
    set_write_limit,
    set_read_limit,
    list_presets,
    apply_preset,
    apply_high_throughput_config,
    apply_conservative_config,
    reset_to_defaults,
    get_desktop_commander_config
)


def main():
    """Main CLI interface for Desktop Commander configuration management."""
    parser = argparse.ArgumentParser(
        description="Desktop Commander MCP Server Configuration Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --show                    Show current read/write limits
  %(prog)s --full                    Show complete configuration
  %(prog)s --set-write-limit 2000    Set write limit to 2000 lines
  %(prog)s --set-read-limit 5000     Set read limit to 5000 lines
  %(prog)s --preset high_throughput  Apply high-throughput preset
  %(prog)s --optimize                Quick optimize for large operations
  %(prog)s --reset                   Reset to default settings
  %(prog)s --presets                 List available presets
        """
    )
    
    # Display options
    display_group = parser.add_argument_group('Display Configuration')
    display_group.add_argument(
        '--show', action='store_true',
        help='Show current read/write limits'
    )
    display_group.add_argument(
        '--full', action='store_true', 
        help='Show complete Desktop Commander configuration'
    )
    display_group.add_argument(
        '--presets', action='store_true',
        help='List available configuration presets'
    )
    
    # Configuration options
    config_group = parser.add_argument_group('Set Configuration')
    config_group.add_argument(
        '--set-write-limit', type=int, metavar='LINES',
        help='Set maximum lines per write_file operation'
    )
    config_group.add_argument(
        '--set-read-limit', type=int, metavar='LINES',
        help='Set maximum lines per read_file operation'
    )
    config_group.add_argument(
        '--preset', metavar='NAME',
        help='Apply configuration preset by name'
    )
    
    # Quick actions
    quick_group = parser.add_argument_group('Quick Actions')
    quick_group.add_argument(
        '--optimize', action='store_true',
        help='Apply high-throughput configuration (write: 2000, read: 5000)'
    )
    quick_group.add_argument(
        '--conservative', action='store_true',
        help='Apply conservative configuration (write: 100, read: 1000)'
    )
    quick_group.add_argument(
        '--reset', action='store_true',
        help='Reset to default configuration (write: 50, read: 1000)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Handle display options
    if args.show:
        show_current_limits()
        return
    
    if args.full:
        show_full_config()
        return
    
    if args.presets:
        list_presets()
        return
    
    # Handle configuration changes
    if args.set_write_limit is not None:
        if args.set_write_limit < 1:
            print("❌ Write limit must be at least 1 line")
            return
        success = set_write_limit(args.set_write_limit)
        if success:
            show_current_limits()
        return
    
    if args.set_read_limit is not None:
        if args.set_read_limit < 1:
            print("❌ Read limit must be at least 1 line")
            return
        success = set_read_limit(args.set_read_limit)
        if success:
            show_current_limits()
        return
    
    if args.preset:
        success = apply_preset(args.preset)
        return
    
    # Handle quick actions
    if args.optimize:
        apply_high_throughput_config()
        return
    
    if args.conservative:
        apply_conservative_config()
        return
    
    if args.reset:
        reset_to_defaults()
        return
    
    # If we get here, no action was specified
    parser.print_help()


def validate_desktop_commander_available():
    """Check if Desktop Commander MCP server is available."""
    try:
        config = get_desktop_commander_config()
        if config:
            print("✅ Desktop Commander MCP server is accessible")
            return True
        else:
            print("❌ Desktop Commander MCP server is not accessible")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to Desktop Commander: {e}")
        return False


def diagnose_config_issues():
    """Diagnose common Desktop Commander configuration issues."""
    print("🔍 DIAGNOSING DESKTOP COMMANDER CONFIGURATION")
    print("="*55)
    
    # Check basic connectivity
    print("1. Testing MCP server connectivity...")
    if not validate_desktop_commander_available():
        print("   ❌ Cannot connect to Desktop Commander MCP server")
        print("   💡 Make sure the MCP server is running")
        return
    
    # Check configuration values
    print("2. Checking configuration values...")
    config = get_desktop_commander_config()
    
    write_limit = config.get("fileWriteLineLimit", 0)
    read_limit = config.get("fileReadLineLimit", 0)
    
    if write_limit < 50:
        print(f"   ⚠️  Write limit is very low: {write_limit} lines")
        print("   💡 Consider increasing with --set-write-limit")
    
    if write_limit > 5000:
        print(f"   ⚠️  Write limit is very high: {write_limit} lines")
        print("   💡 This might cause memory issues")
    
    if read_limit < 100:
        print(f"   ⚠️  Read limit is very low: {read_limit} lines")
        print("   💡 Consider increasing with --set-read-limit")
    
    # Check for common issues
    print("3. Checking for common issues...")
    
    allowed_dirs = config.get("allowedDirectories", [])
    if allowed_dirs:
        print(f"   ⚠️  Directory access is restricted to {len(allowed_dirs)} directories")
        print("   💡 Consider setting allowedDirectories to [] for full access")
    
    blocked_cmds = config.get("blockedCommands", [])
    if blocked_cmds:
        print(f"   ⚠️  {len(blocked_cmds)} commands are blocked")
    
    print("✅ Configuration diagnosis complete")


if __name__ == "__main__":
    # Add special diagnostic command
    if len(sys.argv) > 1 and sys.argv[1] == "diagnose":
        diagnose_config_issues()
    else:
        main()