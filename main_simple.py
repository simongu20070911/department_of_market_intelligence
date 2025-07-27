#!/usr/bin/env python
"""
Simple test of the main system with minimal setup
"""
import asyncio
import os
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai.types import Content, Part
from workflows.root_workflow import RootWorkflowAgent
from tasks import load_research_task

async def main():
    """Main entry point for simple test"""
    
    print("Starting ULTRATHINK_QUANTITATIVEMarketlapha Simple Test...")
    
    # Create the root workflow agent
    root_agent = RootWorkflowAgent(name="RootWorkflow")
    
    # Set up services
    session_service = InMemorySessionService()
    
    # Create runner
    runner = Runner(
        agent=root_agent,
        app_name="ULTRATHINK_QUANTITATIVEMarketlapha",
        session_service=session_service,
    )
    
    # Create session
    session = await session_service.create_session(
        app_name="ULTRATHINK_QUANTITATIVEMarketlapha",
        user_id="researcher"
    )
    
    # Load the research task
    task_description = load_research_task()
    print(f"--- Starting Research Task from tasks/sample_research_task.md ---")
    
    message = Content(parts=[Part(text=task_description)])
    
    # Run the agent
    try:
        async for event in runner.run_async(
            session_id=session.id,
            user_id=session.user_id,
            new_message=message
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        # Extract agent name from the event's author
                        agent_name = event.author or "System"
                        print(f"[{agent_name}]: {part.text}")
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())