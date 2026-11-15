# Agent Workflow Design

## Planner-Executor Pattern

The `PlannerExecutor` class owns the workflow. It does not let agents communicate directly with each other. Each agent receives a typed input contract, executes, and returns a typed output contract. The orchestrator passes outputs to the next agent.

```
PlannerExecutor.plan_visit(form_data)
  │
  ├─► VisitorProfileAgent.run(VisitorProfileAgentInput)
  │       returns VisitorProfileAgentOutput
  │       └─ profile saved to WorkflowState.visitor_profile_output
  │
  ├─► ExhibitRetrievalAgent.run(ExhibitRetrievalAgentInput)
  │       input: visitor_profile from step 1
  │       returns ExhibitRetrievalAgentOutput
  │       └─ saved to WorkflowState.retrieval_output
  │
  ├─► RoutePlannerAgent.run(RoutePlannerAgentInput)
  │       input: visitor_profile + candidate_exhibit_ids from step 2
  │       calls: WalkingDistanceTool, OpeningHoursTool, CrowdStatusTool
  │       returns RoutePlannerAgentOutput
  │
  ├─► CommentaryWriterAgent.run(CommentaryWriterAgentInput)
  │       input: visitor_profile + route + retrieved_evidence
  │       returns CommentaryWriterAgentOutput
  │
  └─► GuideManagerAgent.run(GuideManagerAgentInput)
          input: all previous outputs + visit_id
          returns (VisitGuide, GuideManagerAgentOutput)
```

## WorkflowState

A single `WorkflowState` object is created per planning execution. It records:
- visit_id, visitor_id
- start/finish timestamps
- status: running | completed | failed
- trace: list of WorkflowTraceEntry (agent_name, status, started_at, completed_at, duration_ms, input_summary, output_summary, error_message)

The trace is attached to the final VisitGuide and exposed via GET /api/visits/{visit_id}/trace.

## Retries

Each agent is wrapped in a retry loop (MAX_RETRIES = 2). On transient failure, the orchestrator retries with the same input. On final failure, the trace entry is marked FAILED and the orchestration raises, returning an error to the API.

## Semantic Kernel Integration

`framework_adapter.py` wraps each agent as a Semantic Kernel `@kernel_function` inside an `AgentPlugin`. This makes each agent a discoverable SK skill callable by the kernel planner. In sequential fallback mode (when SK is not installed), the orchestrator runs agents directly in order.

## Difference from a Single Chatbot

| Dimension | Single Chatbot | This System |
|---|---|---|
| Responsibility | One LLM prompt handles all tasks | Each agent has a dedicated, isolated responsibility |
| Contracts | Implicit, untyped | Typed Pydantic input/output per agent |
| Observability | Black box | Full WorkflowTraceEntry per agent in every guide |
| Replanning | Restart from scratch | Orchestrator re-runs agents 2–5 with updated state |
| Tools | LLM may hallucinate distances | Tools provide deterministic, seeded data |
| Memory | Stateless per session | Persistent MongoDB memory across sessions |
