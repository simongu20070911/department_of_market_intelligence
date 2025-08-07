# /department_of_market_intelligence/prompts/components/orchestrator_tasks.py
"""Task definitions for the Orchestrator agent."""

GENERATE_IMPLEMENTATION_PLAN_TASK = """
Your primary task is to create a detailed implementation plan based on the approved research plan.
Decompose the research plan into parallelizable subtasks, define integration points, and specify success criteria for each subtask.
"""

REFINE_IMPLEMENTATION_PLAN_TASK = """
Your task is to refine the implementation plan based on the feedback from the validation team.
Address each point of feedback, explaining how you have incorporated it into the revised plan.
"""