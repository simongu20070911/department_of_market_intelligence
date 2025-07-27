# /department_of_market_intelligence/main.py
import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai.types import Content, Part
from .workflows.root_workflow import RootWorkflowAgent
from .config import TASKS_DIR

async def main():
    # Initialize ADK services for this run
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()

    # The root of our agentic system
    root_agent = RootWorkflowAgent(name="MarketAlpha_Root")

    runner = Runner(
        agent=root_agent,
        app_name="ULTRATHINK_QUANTITATIVE",
        session_service=session_service,
        artifact_service=artifact_service,
    )

    # Prepare the initial session state
    task_file = f"{TASKS_DIR}/sample_research_task.md"
    initial_state = {"task_file_path": task_file}
    
    # Create a session for this research task
    session = await session_service.create_session(
        app_name="ULTRATHINK_QUANTITATIVE",
        user_id="quant_team",
        state=initial_state
    )

    print(f"--- Starting Research Task from {task_file} ---")
    
    # Start the process with an initial message (can be empty)
    start_message = Content(parts=[Part(text="Begin the research process.")])
    
    async for event in runner.run_async(
        session_id=session.id,
        user_id=session.user_id,
        new_message=start_message
    ):
        # You can process and print events here for real-time monitoring
        if event.content and event.content.parts and event.content.parts[0].text:
            print(f"[{event.author}]: {event.content.parts[0].text.strip()}")

if __name__ == "__main__":
    asyncio.run(main())