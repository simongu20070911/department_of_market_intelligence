● Here's what I envision for a centralized prompt construction system:

  Centralized Prompt Architecture

  1. Directory Structure

  department_of_market_intelligence/
  └── prompts/
      ├── __init__.py
      ├── base.py                  # Base templates and common sections
      ├── agents/
      │   ├── __init__.py
      │   ├── chief_researcher.py  # Chief Researcher prompts
      │   ├── orchestrator.py      # Orchestrator prompts
      │   ├── executor.py          # Experiment Executor prompts
      │   ├── validators.py        # All validator prompts
      │   └── coder.py            # Coder prompts
      ├── components/
      │   ├── __init__.py
      │   ├── personas.py         # Reusable persona descriptions
      │   ├── protocols.py        # Communication protocols
      │   ├── tasks.py           # Task-specific instructions
      │   └── constraints.py      # Common constraints and rules
      └── builder.py              # Prompt composition utilities

  2. Base Components (prompts/base.py)

  # Base communication protocol used by ALL agents
  COMMUNICATION_PROTOCOL = """
  ### COMMUNICATION PROTOCOL - CRITICAL ###
  ALWAYS start your response with:
  🤔 [{agent_name}]: Examining the session state to understand what's needed...

  Then EXPLICITLY mention:
  - 📁 Working directory: {outputs_dir}
  - 📖 Reading from: [specific file paths]
  - 💾 Writing to: [specific file paths] 
  - 🎯 Current task: {current_task}
  """

  # Base context template
  BASE_CONTEXT = """
  ### Context & State ###
  You will operate based on the 'current_task' key in the session state: {current_task}
  Today's date is: {current_date}
  Current year: {current_year}
  """

  # Standard output format
  OUTPUT_FORMAT = """
  ### Output Format ###
  You MUST end every response with "<end of output>".
  """

  3. Component Library (prompts/components/)

  personas.py:
  CHIEF_RESEARCHER_PERSONA = """
  ### Persona ###
  You are the Chief Researcher for the ULTRATHINK_QUANTITATIVE Market Alpha department. 
  Your work is defined by its meticulousness, statistical rigor, and proactive pursuit 
  of significant insights. You do not accept ambiguity.
  """

  ORCHESTRATOR_PERSONA = """
  ### Persona ###
  You are the Orchestrator for ULTRATHINK_QUANTITATIVE Market Alpha. Your expertise 
  is in decomposing complex quantitative research plans into MAXIMALLY PARALLEL 
  execution graphs...
  """

  tasks.py:
  # Reusable task templates
  GENERATE_INITIAL_PLAN_TASK = """
  ### Task: 'generate_initial_plan' ###
  If the current task is 'generate_initial_plan':
  1.  Read the research task description from: {task_file_path}
  2.  Generate a comprehensive research plan including:
      - Clear hypothesis
      - Data sourcing protocols
      - Statistical tests (t-tests, regression, stationarity)
      - Required outputs and metrics
  3.  Save to: {outputs_dir}/planning/research_plan_v0.md
  4.  Update session state with artifact information
  """

  4. Prompt Builder (prompts/builder.py)

  from typing import Dict, List, Optional

  class PromptBuilder:
      """Builds prompts from components with validation."""

      def __init__(self):
          self.sections = []
          self.required_vars = set()

      def add_section(self, template: str, required_vars: List[str] = None):
          """Add a section to the prompt."""
          self.sections.append(template)
          if required_vars:
              self.required_vars.update(required_vars)
          return self

      def add_persona(self, persona: str):
          """Add persona section."""
          return self.add_section(persona)

      def add_communication_protocol(self):
          """Add standard communication protocol."""
          from .base import COMMUNICATION_PROTOCOL
          return self.add_section(COMMUNICATION_PROTOCOL, ['agent_name', 'outputs_dir', 'current_task'])

      def add_context(self):
          """Add standard context section."""
          from .base import BASE_CONTEXT
          return self.add_section(BASE_CONTEXT, ['current_task', 'current_date', 'current_year'])

      def add_tasks(self, tasks: List[str]):
          """Add multiple task sections."""
          for task in tasks:
              self.add_section(task)
          return self

      def add_output_format(self):
          """Add standard output format."""
          from .base import OUTPUT_FORMAT
          return self.add_section(OUTPUT_FORMAT)

      def build(self) -> str:
          """Build the final prompt."""
          return "\n\n".join(self.sections)

      def validate_vars(self, provided_vars: Dict[str, any]) -> bool:
          """Validate that all required variables are provided."""
          return self.required_vars.issubset(provided_vars.keys())

  5. Agent Prompt Definitions (prompts/agents/chief_researcher.py)

  from ..builder import PromptBuilder
  from ..components.personas import CHIEF_RESEARCHER_PERSONA
  from ..components.tasks import (
      GENERATE_INITIAL_PLAN_TASK,
      REFINE_PLAN_TASK,
      GENERATE_FINAL_REPORT_TASK
  )

  def build_chief_researcher_prompt() -> str:
      """Build the Chief Researcher prompt from components."""
      builder = PromptBuilder()

      return builder\
          .add_persona(CHIEF_RESEARCHER_PERSONA)\
          .add_communication_protocol()\
          .add_context()\
          .add_section("### Important Time Context ###\nRemember: You cannot analyze future data. Any analysis period
   must end on or before today's date.")\
          .add_tasks([
              GENERATE_INITIAL_PLAN_TASK,
              REFINE_PLAN_TASK,
              GENERATE_FINAL_REPORT_TASK
          ])\
          .add_output_format()\
          .build()

  # Export the built prompt
  CHIEF_RESEARCHER_INSTRUCTION = build_chief_researcher_prompt()

  6. Usage in Agent Files

  # agents/chief_researcher.py
  from ..prompts.agents.chief_researcher import CHIEF_RESEARCHER_INSTRUCTION

  def get_chief_researcher_agent():
      return LlmAgent(
          model=get_llm_model(config.CHIEF_RESEARCHER_MODEL),
          name="Chief_Researcher",
          instruction=CHIEF_RESEARCHER_INSTRUCTION,
          tools=tools
      )

  7. Benefits of This System

  1. DRY Principle: Communication protocol defined once, used everywhere
  2. Modularity: Mix and match components for different agents
  3. Validation: Can validate required variables before runtime
  4. Versioning: Easy to track prompt changes in git
  5. Testing: Can unit test individual components
  6. Consistency: Enforces standard structure across all agents
  7. Maintainability: Update one component, affects all agents using it

  8. Advanced Features

  # Dynamic prompt generation based on context
  class ContextAwarePromptBuilder(PromptBuilder):
      def add_context_specific_tasks(self, context: str):
          """Add tasks based on validation context."""
          if context == "research_plan":
              self.add_section(RESEARCH_PLAN_VALIDATION_TASKS)
          elif context == "implementation_manifest":
              self.add_section(IMPLEMENTATION_VALIDATION_TASKS)
          return self

  This system would replace the current mess of inline prompts, duplicated instructions, and inconsistent formatting
  with a clean, maintainable, and extensible prompt management system.
