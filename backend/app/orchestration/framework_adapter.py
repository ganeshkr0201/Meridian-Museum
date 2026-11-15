"""
Framework Adapter — Semantic Kernel Integration
Wraps each museum agent as a Semantic Kernel plugin function so the SK
kernel can coordinate them in a planner-executor pattern.

NOTE: Microsoft Agent Framework is not publicly available as an open-source
pip package. This project uses Semantic Kernel (semantic-kernel), which is
Microsoft's production-ready agent/orchestration framework for Python.
See README.md for detailed justification.
"""

from __future__ import annotations
import logging
from typing import Any

try:
    import semantic_kernel as sk
    from semantic_kernel.functions import kernel_function
    SK_AVAILABLE = True
except ImportError:
    SK_AVAILABLE = False
    logging.getLogger(__name__).warning(
        "semantic-kernel not installed. Orchestrator will run in sequential fallback mode."
    )

logger = logging.getLogger(__name__)


def build_kernel() -> Any:
    """Build and return a Semantic Kernel kernel instance, or None if unavailable."""
    if not SK_AVAILABLE:
        return None
    kernel = sk.Kernel()
    logger.info("Semantic Kernel instance created.")
    return kernel


class AgentPlugin:
    """
    Semantic Kernel plugin that exposes museum agents as kernel functions.
    Each method decorated with @kernel_function becomes a discoverable
    SK skill callable by the planner.
    """

    def __init__(self, orchestrator: Any):
        self._orchestrator = orchestrator

    if SK_AVAILABLE:
        @kernel_function(name="run_visitor_profile_agent", description="Validate visitor input and build profile")
        async def run_visitor_profile_agent(self, payload: str) -> str:
            import json
            data = json.loads(payload)
            result = await self._orchestrator._run_visitor_profile_agent(data)
            return json.dumps({"status": "completed", "visitor_id": result.visitor_profile.visitor_id})

        @kernel_function(name="run_exhibit_retrieval_agent", description="Retrieve relevant exhibit evidence via RAG")
        async def run_exhibit_retrieval_agent(self, payload: str) -> str:
            import json
            result = await self._orchestrator._run_retrieval_agent()
            return json.dumps({"status": "completed", "candidates": result.candidate_exhibit_ids})

        @kernel_function(name="run_route_planner_agent", description="Plan the visitor route using tools")
        async def run_route_planner_agent(self, payload: str) -> str:
            import json
            result = await self._orchestrator._run_route_planner()
            return json.dumps({"status": "completed", "stops": len(result.route)})

        @kernel_function(name="run_commentary_writer_agent", description="Write grounded commentary for each stop")
        async def run_commentary_writer_agent(self, payload: str) -> str:
            import json
            result = await self._orchestrator._run_commentary_writer()
            return json.dumps({"status": "completed", "commentaries": len(result.commentaries)})

        @kernel_function(name="run_guide_manager_agent", description="Compile and validate the final guide")
        async def run_guide_manager_agent(self, payload: str) -> str:
            import json
            guide, manager_out = await self._orchestrator._run_guide_manager()
            return json.dumps({"status": "completed", "valid": manager_out.valid})
