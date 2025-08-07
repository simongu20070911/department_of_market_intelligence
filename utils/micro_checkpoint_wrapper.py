"""
A reusable wrapper for adding micro-checkpointing capabilities to agents.
"""

import asyncio
from typing import Dict, Any, List, AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event

from .. import config
from .state_adapter import get_domi_state
from .checkpoint_manager import CheckpointManager


from typing import Callable, Optional, Any
from pydantic import Field


class MicroCheckpointWrapper(BaseAgent):
    """
    A wrapper that adds micro-checkpointing capabilities to any agent.
    """
    agent_factory: Optional[Callable[[], BaseAgent]] = Field(default=None, exclude=True)
    _agent: Optional[BaseAgent] = None
    
    def __init__(self, agent_factory: Callable[[], BaseAgent], **kwargs):
        super().__init__(**kwargs)
        # Use object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, 'agent_factory', agent_factory)
        object.__setattr__(self, '_agent', None)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Executes the agent with micro-checkpointing.
        """
        domi_state = get_domi_state(ctx)
        task_id = domi_state.task_id
        checkpoint_manager = CheckpointManager(task_id)

        # Always initialize the agent if not already done
        if getattr(self, '_agent', None) is None:
            agent = self.agent_factory()
            object.__setattr__(self, '_agent', agent)

        agent = getattr(self, '_agent', None)
        if agent is None:
            raise RuntimeError("Failed to initialize agent")
            
        if not config.ENABLE_MICRO_CHECKPOINTS:
            print(f"[{self.name}]: Micro-checkpoints disabled, running standard execution.")
            async for event in agent.run_async(ctx):
                yield event
            return

        # Micro-checkpointing enabled - run with checkpointing logic
        print(f"[{self.name}]: Micro-checkpoints enabled, running with checkpoint support.")
        
        # For now, just run the agent normally until full micro-checkpoint logic is implemented
        # TODO: Implement full micro-checkpoint logic with operation tracking
        async for event in agent.run_async(ctx):
            yield event