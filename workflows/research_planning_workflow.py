# /department_of_market_intelligence/workflows/research_planning_workflow.py
from google.adk.agents import SequentialAgent, LoopAgent
from ..agents.chief_researcher import get_chief_researcher_agent
from ..agents.validators import get_junior_validator_agent, get_senior_validator_agent, MetaValidatorCheckAgent
from .. import config

def get_research_planning_workflow():
    # Define the sequence of actions within one loop iteration
    refinement_sequence = SequentialAgent(
        name="PlanRefinementSequence",
        sub_agents=[
            get_chief_researcher_agent(),
            get_junior_validator_agent(),
            get_senior_validator_agent(),
            MetaValidatorCheckAgent(name="MetaValidatorCheck"),
        ]
    )

    # The LoopAgent will run the sequence repeatedly until the MetaValidatorCheck escalates.
    planning_loop = LoopAgent(
        name="ResearchPlanningLoop",
        max_iterations=config.MAX_PLAN_REFINEMENT_LOOPS,
        sub_agents=[refinement_sequence]
    )
    return planning_loop