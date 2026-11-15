# Architecture Document

## System Overview

The Meridian Museum Personalised Exhibit Guide is a full-stack application demonstrating a genuine multi-agent workflow, not a single chatbot pretending to be multiple agents.

## Component Map

```
┌─────────────────────────────────────────────────────┐
│                   React Frontend                     │
│  Home │ Plan Visit │ Guide │ Crowd │ Memory │ Eval  │
└───────────────────┬─────────────────────────────────┘
                    │ HTTP REST (Axios)
                    ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                │
│   /api/visits/plan  /api/galleries  /api/evaluation │
└───────────────────┬─────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│          PlannerExecutor (Semantic Kernel)            │
│                                                      │
│  1. VisitorProfileAgent  ◄──► MongoDB (VisitorMem)  │
│  2. ExhibitRetrievalAgent ◄─► ChromaDB (61 chunks)  │
│  3. RoutePlannerAgent                               │
│       ├─ WalkingDistanceTool (Dijkstra graph)        │
│       ├─ OpeningHoursTool (seeded data)              │
│       └─ CrowdStatusTool (in-memory + DB)           │
│  4. CommentaryWriterAgent (demo / OpenAI)            │
│  5. GuideManagerAgent (validation + assembly)        │
└─────────────────────────────────────────────────────┘
```

## Data Flow

1. Visitor submits form → POST /api/visits/plan
2. PlannerExecutor starts WorkflowState (visit_id, timestamp)
3. VisitorProfileAgent normalises input, reads/writes MongoDB memory
4. ExhibitRetrievalAgent embeds interests, queries ChromaDB, returns ranked evidence
5. RoutePlannerAgent scores candidates, calls walking/hours/crowd tools, builds ordered stops
6. CommentaryWriterAgent writes grounded 2–4 sentence notes per stop (demo: deterministic; openai: LLM)
7. GuideManagerAgent recalculates totals server-side, checks constraints, computes coverage
8. VisitGuide (with workflow_trace) returned to frontend

## Why Semantic Kernel?

Semantic Kernel is Microsoft's open-source Python agent framework (pypi: `semantic-kernel`). It provides:
- `Kernel` as the central coordinator
- `@kernel_function` decorator for registering agent capabilities as SK plugins
- Native support for planner-executor patterns
- Compatible with OpenAI and Azure OpenAI

Microsoft Agent Framework is not available as a public pip package; Semantic Kernel is Microsoft's recommended replacement and is fully documented at microsoft.github.io/semantic-kernel.

## Security Decisions

- All secrets in environment variables (`.env`)
- `.env` excluded from git via `.gitignore`
- CORS restricted to configured frontend origin
- No personal data logged
- Parameterised MongoDB ODM operations (Motor)
- Input validated via Pydantic v2 at all API boundaries
