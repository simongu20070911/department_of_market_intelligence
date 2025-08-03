#!/usr/bin/env python3
"""
Progress monitor for the Market Intelligence system.
Shows only important workflow events and agent outputs.
"""

import asyncio
import sys
import re
from datetime import datetime
from department_of_market_intelligence.main import main as original_main
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai.types import Content, Part
from department_of_market_intelligence.workflows.root_workflow_context_aware import RootWorkflowAgentContextAware
from department_of_market_intelligence.config import TASKS_DIR

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

class ProgressMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.current_phase = None
        self.current_agent = None
    
    def timestamp(self):
        elapsed = datetime.now() - self.start_time
        return f"[{elapsed.seconds:3d}s]"
    
    def phase(self, phase_name):
        self.current_phase = phase_name
        print(f"\n{self.timestamp()} {BOLD}{GREEN}━━━ {phase_name} ━━━{RESET}")
    
    def agent_start(self, agent_name):
        self.current_agent = agent_name
        print(f"{self.timestamp()} {CYAN}▶ {agent_name} starting...{RESET}")
    
    def agent_output(self, agent_name, message):
        # Clean up the message
        clean_msg = message.strip()
        if clean_msg and clean_msg != "<end of output>":
            # Truncate very long messages
            if len(clean_msg) > 200:
                clean_msg = clean_msg[:197] + "..."
            print(f"{self.timestamp()} {YELLOW}  {agent_name}:{RESET} {clean_msg}")
    
    def tool_call(self, tool_name, args):
        # Only show important tool calls
        important_tools = ['read_file', 'write_file', 'execute_command']
        if tool_name in important_tools:
            arg_str = str(args).get('path', str(args))[:50]
            print(f"{self.timestamp()} {MAGENTA}  └─ {tool_name}:{RESET} {arg_str}")
    
    def error(self, message):
        print(f"{self.timestamp()} {BOLD}❌ ERROR:{RESET} {message}")
    
    def success(self, message):
        print(f"{self.timestamp()} {BOLD}✅ {message}{RESET}")

monitor = ProgressMonitor()

async def monitored_main():
    """Run the main workflow with progress monitoring."""
    # Initialize ADK services
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    
    # Create root agent
    root_agent = RootWorkflowAgentContextAware(name="MarketAlpha_Root")
    
    runner = Runner(
        agent=root_agent,
        app_name="ULTRATHINK_QUANTITATIVE",
        session_service=session_service,
        artifact_service=artifact_service,
    )
    
    # Prepare initial session state
    task_file = f"{TASKS_DIR}/sample_research_task.md"
    initial_state = {"task_file_path": task_file}
    
    session = await session_service.create_session(
        app_name="ULTRATHINK_QUANTITATIVE",
        user_id="quant_team",
        state=initial_state
    )
    
    monitor.phase("INITIALIZATION")
    monitor.success(f"Session created with task: {task_file}")
    
    # Start the process
    start_message = Content(parts=[Part(text="Begin the research process.")])
    
    current_workflow_phase = None
    
    async for event in runner.run_async(
        session_id=session.id,
        user_id=session.user_id,
        new_message=start_message
    ):
        if event.content and event.content.parts and event.content.parts[0].text:
            text = event.content.parts[0].text.strip()
            
            # Detect phase changes
            if "ROOT WORKFLOW:" in text:
                if "Research Planning Phase" in text:
                    monitor.phase("RESEARCH PLANNING")
                elif "Implementation & Execution Phase" in text:
                    monitor.phase("IMPLEMENTATION & EXECUTION")
                elif "Final Reporting Phase" in text:
                    monitor.phase("FINAL REPORTING")
                elif "Process Complete" in text:
                    monitor.phase("COMPLETED")
            
            # Track agent outputs
            elif event.author:
                agent_name = event.author
                # Filter out system messages
                if not any(skip in text for skip in ["ASYNC kwargs", "RAW RESPONSE", "Loading", "auth_config"]):
                    monitor.agent_output(agent_name, text)
    
    monitor.success("Research process completed successfully!")

if __name__ == "__main__":
    print(f"{BOLD}{CYAN}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║     ULTRATHINK_QUANTITATIVE Market Intelligence         ║{RESET}")
    print(f"{BOLD}{CYAN}║                  Progress Monitor                        ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════╝{RESET}")
    
    try:
        asyncio.run(monitored_main())
    except KeyboardInterrupt:
        print(f"\n{monitor.timestamp()} {YELLOW}Process interrupted by user.{RESET}")
    except Exception as e:
        monitor.error(str(e))
        raise