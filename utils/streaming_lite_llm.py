import uuid
from google.adk.models.lite_llm import LiteLlm

class StreamingLiteLlm(LiteLlm):
    async def acompletion(self, **kwargs):
        if "tools" in kwargs:
            for tool in kwargs["tools"]:
                if "function" in tool and "id" not in tool["function"]:
                    tool["function"]["id"] = str(uuid.uuid4())
        return await super().acompletion(**kwargs)