"""AgentCore Runtime agent definition and tool registration.

AgentCore's China-region SDK/model wiring is the design's A1 assumption and must
be validated in an aws-cn account (it cannot run in a public sandbox). This
module therefore ships the agent contract (system prompt + JSON-schema tools)
and a handler that AgentCore can invoke once the A1 check passes. The same
tool dispatch is used by the LangGraph fallback in agent/langgraph_main.py.
"""

from __future__ import annotations

from typing import Any, Dict

from agent.tools import TOOL_DEFINITIONS, ToolRegistry
from agent.orchestrator import SYSTEM_PROMPT


def build_agentcore_agent_definition(model: str = "qwen2.5-7b-instruct") -> Dict[str, Any]:
    """Return the AgentCore agent contract (platform SDK binding happens in IaC)."""
    return {
        "name": "knowledge-assistant",
        "description": "组织内部知识助手：检索知识库、读取长期记忆、生成回答并写回记忆。",
        "model": model,
        "system_prompt": SYSTEM_PROMPT,
        "tools": TOOL_DEFINITIONS,
    }


def build_agentcore_handler(registry: ToolRegistry):
    """Wrap the ToolRegistry for the AgentCore tool-call loop."""

    def handle(tool_name: str, arguments: Dict[str, Any], user_id: str = "default") -> Any:
        return registry.dispatch(tool_name, arguments, user_id)

    return handle


if __name__ == "__main__":
    import json

    print(json.dumps(build_agentcore_agent_definition(), ensure_ascii=False, indent=2))
