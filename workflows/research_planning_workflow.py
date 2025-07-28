# /department_of_market_intelligence/workflows/research_planning_workflow.py
from google.adk.agents import SequentialAgent, LoopAgent
from ..agents.chief_researcher import get_chief_researcher_agent
from ..agents.validators import get_junior_validator_agent, get_senior_validator_agent, MetaValidatorCheckAgent, get_parallel_final_validation_agent
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
    max_iterations = config.MAX_PLAN_REFINEMENT_LOOPS
    if config.DRY_RUN_MODE:
        max_iterations = min(max_iterations, config.MAX_DRY_RUN_ITERATIONS)
        print(f"DRY RUN MODE: Limiting planning loop to {max_iterations} iterations")
    
    planning_loop = LoopAgent(
        name="ResearchPlanningLoop",
        max_iterations=max_iterations,
        sub_agents=[refinement_sequence]
    )
    
    # Create the complete workflow: main loop + parallel final validation
    complete_planning_workflow = SequentialAgent(
        name="CompletePlanningWorkflow",
        sub_agents=[
            planning_loop,
            get_parallel_final_validation_agent()
        ]
    )
    
    return complete_planning_workflow