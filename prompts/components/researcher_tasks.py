# /department_of_market_intelligence/prompts/components/researcher_tasks.py
"""Task definitions for the Chief Researcher agent."""

GENERATE_INITIAL_PLAN_TASK = """
Your primary task is to generate a comprehensive initial research plan based on the provided task description.
The plan should be detailed, outlining the research questions, methodology, data requirements, and success criteria.
"""

REFINE_PLAN_TASK = """
Your task is to refine the research plan based on the feedback from the validation team.
Address each point of feedback, explaining how you have incorporated it into the revised plan.
"""

FINAL_REPORT_TASK = """
Your final task is to synthesize all the findings and generate a comprehensive final report.
The report should be well-structured, clearly presenting the results, analysis, and conclusions.
"""