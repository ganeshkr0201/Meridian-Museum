# PROJECT_SPEC.md — Q26 Museum Exhibit Curation and Visitor Guide

## Project Title
Meridian Museum — Personalised Exhibit Guide (Q26)

## Assessment
Bloom's Taxonomy: L4, L5, L6 | Planner | 30 Marks

## Group
- 12317780 — Ganesh Kumar
- 12320064 — Saurav

## Purpose
A personalised museum visit guide that creates a custom route and factually grounded commentary for each selected exhibit. Demonstrates genuine multi-agent workflow, planner-executor coordination, RAG over museum content, shared visitor-preference memory, and crowd-aware replanning.

## Five Agents

| Agent | Module | Responsibility |
|---|---|---|
| Visitor Profile Agent | `agents/visitor_profile_agent.py` | Validate input, resolve preferences, read/write shared memory |
| Exhibit Retrieval Agent | `agents/exhibit_retrieval_agent.py` | RAG over catalogue + curator notes via ChromaDB |
| Route Planner Agent | `agents/route_planner_agent.py` | Heuristic route planning with walking, hours, crowd tools |
| Commentary Writer Agent | `agents/commentary_writer_agent.py` | Grounded exhibit commentary with citations |
| Guide Manager Agent | `agents/guide_manager_agent.py` | Validation, compilation, interest coverage |

## Orchestration
- `orchestration/planner_executor.py` — Semantic Kernel-backed planner-executor
- `orchestration/workflow_state.py` — Shared mutable workflow state with full trace
- `orchestration/framework_adapter.py` — SK plugin wrappers for each agent

## RAG Pipeline
1. Load 13 curator notes + 12 catalogue entries
2. Chunk with 2-sentence windows
3. Embed with `all-MiniLM-L6-v2` (384 dimensions)
4. Store 61 chunks in ChromaDB (cosine similarity)
5. Retrieve top-k per visitor query
6. Pass evidence to Commentary Writer with source IDs

## Tools
- `tools/walking_distance.py` — Dijkstra shortest path on 6-edge museum graph
- `tools/opening_hours.py` — Seeded gallery hours check
- `tools/crowd_status.py` — In-memory crowd state with penalty minutes

## Shared Memory
- `memory/visitor_memory.py` — MongoDB-backed (in-memory fallback)
- Stores: interests, accessibility, language, commentary preference, visited exhibits, feedback, history
- All agents read; Visitor Profile Agent writes on each session

## Crowd-Aware Replanning
1. Visitor marks gallery busy via UI
2. `visit_service.replan()` calls `PlannerExecutor.replan()`
3. Busy gallery excluded from candidates
4. Completed stops preserved, elapsed time subtracted
5. Full re-run of agents 2–5 with remaining budget
6. Before/after comparison displayed in Crowd Control page

## Evaluation
- 8 seeded visitor profiles (`data/visitor_profiles.json`)
- Metrics: Time Budget Fit Rate, Interest Coverage Rate, Accessibility Rate, Opening Hours Rate
- Output: JSON + Markdown reports in `evaluation_reports/`

## Acceptance Checklist

### Multi-agent
- [x] Five agents as separate modules with typed contracts
- [x] Semantic Kernel used for orchestration
- [x] Planner-executor coordination implemented
- [x] Workflow traces show real execution with timestamps and durations

### RAG and Memory
- [x] Exhibit catalogue and curator notes indexed in ChromaDB (61 chunks)
- [x] Retrieval returns relevant evidence with source references
- [x] Commentary grounded in retrieved evidence
- [x] Visitor memory persists across sessions
- [x] Every agent can access shared memory service
- [x] Visitor can view, edit, and clear memory

### Route Planning
- [x] Walking-distance tool implemented and used (Dijkstra)
- [x] Opening-hours tool implemented and used
- [x] Route respects time budget
- [x] Route respects accessibility constraints
- [x] Skipped items include reason codes and human-readable explanations

### Crowd-Aware Add-on
- [x] User can mark a gallery busy
- [x] Remaining route replanned without restarting
- [x] Completed stops remain completed
- [x] Remaining time respected
- [x] Before/after route and explanation displayed

### Evaluation
- [x] Eight visitor profiles seeded
- [x] Evaluation runs for all eight profiles
- [x] Time-budget fit rate calculated from actual routes
- [x] Interest coverage calculated from stated interests
- [x] Results saved as JSON and Markdown report

### Frontend and Run
- [x] All required pages work (Home, Plan, Guide, Crowd, Memory, Evaluation, About)
- [x] No inert buttons
- [x] Demo mode works without paid API credentials
- [x] Backend starts with `uvicorn app.main:app --reload`
- [x] Frontend starts with `npm run dev`
- [x] README includes all setup commands
