#!/usr/bin/env python3
"""Command-line interface for checkpoint management and task execution."""

import argparse
import asyncio
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from department_of_market_intelligence import config
from department_of_market_intelligence.utils.checkpoint_manager import checkpoint_manager
from department_of_market_intelligence.main import main


def list_checkpoints():
    """List all available checkpoints."""
    checkpoints = checkpoint_manager.list_checkpoints()
    
    if not checkpoints:
        print("📋 No checkpoints found")
        return
    
    print(f"📋 Available Checkpoints for Task: {config.TASK_ID}")
    print("=" * 80)
    print(f"{'ID':<50} {'Phase':<20} {'Step':<15} {'Date':<20}")
    print("-" * 80)
    
    for cp in checkpoints:
        timestamp = datetime.fromisoformat(cp['timestamp'].replace('Z', '+00:00'))
        date_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"{cp['checkpoint_id'][:47]:<50} {cp['phase']:<20} {cp['step']:<15} {date_str:<20}")


def show_recovery_info():
    """Show recovery information."""
    info = checkpoint_manager.get_recovery_info()
    
    print(f"🔍 Recovery Information")
    print("=" * 50)
    print(f"Task ID: {info['task_id']}")
    print(f"Available Checkpoints: {info['checkpoints_available']}")
    print(f"Can Resume: {'✅ Yes' if info['can_resume'] else '❌ No'}")
    
    if info['latest_checkpoint']:
        print(f"Latest Checkpoint: {info['latest_checkpoint']}")
    
    print(f"Checkpoints Directory: {info['checkpoints_dir']}")
    print(f"Outputs Directory: {info['outputs_dir']}")


def delete_checkpoint(checkpoint_id: str):
    """Delete a specific checkpoint."""
    if checkpoint_manager.delete_checkpoint(checkpoint_id):
        print(f"✅ Checkpoint deleted: {checkpoint_id}")
    else:
        print(f"❌ Failed to delete checkpoint: {checkpoint_id}")


def cleanup_checkpoints(keep_count: int):
    """Cleanup old checkpoints."""
    checkpoint_manager.cleanup_old_checkpoints(keep_count)


async def run_task(task_id: str = None, resume_from: str = None):
    """Run or resume a research task."""
    if task_id:
        # Update task ID in config
        config.TASK_ID = task_id
        print(f"🎯 Task ID set to: {task_id}")
    
    if resume_from:
        print(f"🔄 Resuming from checkpoint: {resume_from}")
        await main(resume_from_checkpoint=resume_from)
    else:
        print(f"🚀 Starting new task: {config.TASK_ID}")
        await main()


def main_cli():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="ULTRATHINK_QUANTITATIVEMarketAlpha Checkpoint Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all checkpoints
  python checkpoint_cli.py list
  
  # Show recovery info
  python checkpoint_cli.py info
  
  # Start a new task
  python checkpoint_cli.py run --task-id "market_research_2025"
  
  # Resume from latest checkpoint
  python checkpoint_cli.py run --resume
  
  # Resume from specific checkpoint
  python checkpoint_cli.py run --resume-from "research_planning_phase_complete_2025-07-28T..."
  
  # Delete a checkpoint
  python checkpoint_cli.py delete "checkpoint_id"
  
  # Cleanup old checkpoints (keep 5 most recent)
  python checkpoint_cli.py cleanup --keep 5
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    subparsers.add_parser('list', help='List all available checkpoints')
    
    # Info command
    subparsers.add_parser('info', help='Show recovery information')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run or resume a research task')
    run_parser.add_argument('--task-id', type=str, help='Task ID to run')
    run_parser.add_argument('--resume', action='store_true', help='Resume from latest checkpoint')
    run_parser.add_argument('--resume-from', type=str, help='Resume from specific checkpoint ID')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a specific checkpoint')
    delete_parser.add_argument('checkpoint_id', help='Checkpoint ID to delete')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup old checkpoints')
    cleanup_parser.add_argument('--keep', type=int, default=10, help='Number of checkpoints to keep (default: 10)')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show current configuration')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_checkpoints()
        
    elif args.command == 'info':
        show_recovery_info()
        
    elif args.command == 'run':
        resume_from = None
        if args.resume:
            resume_from = checkpoint_manager._get_latest_checkpoint()
            if not resume_from:
                print("❌ No checkpoints available for resumption")
                return
        elif args.resume_from:
            resume_from = args.resume_from
        
        asyncio.run(run_task(args.task_id, resume_from))
        
    elif args.command == 'delete':
        delete_checkpoint(args.checkpoint_id)
        
    elif args.command == 'cleanup':
        cleanup_checkpoints(args.keep)
        
    elif args.command == 'config':
        print(f"Configuration:")
        print(f"  Task ID: {config.TASK_ID}")
        print(f"  Enable Checkpointing: {config.ENABLE_CHECKPOINTING}")
        print(f"  Checkpoint Interval: {config.CHECKPOINT_INTERVAL}")
        print(f"  Dry Run Mode: {config.DRY_RUN_MODE}")
        print(f"  Outputs Dir: {config.OUTPUTS_DIR}")
        print(f"  Checkpoints Dir: {config.CHECKPOINTS_DIR}")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main_cli()