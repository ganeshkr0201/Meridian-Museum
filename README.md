# Museum Exhibit Guide — Q26

**Meridian Museum Personalised Exhibit Guide**
A complete multi-agent museum visit planner with RAG, shared memory, crowd-aware replanning, and a React dashboard.

> Fictional demonstration dataset — Meridian Museum of World Cultures.

---

## Group Members

| Student ID | Name | Suggested Responsibility |
|---|---|---|
| 12317780 | Ganesh Kumar | Backend (agents, orchestration, RAG, tools, evaluation) |
| 12320064 | Saurav | Frontend (React pages, API integration, UI/UX, documentation) |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, React Router, Axios |
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| Agent Framework | **Semantic Kernel** (Microsoft's open-source Python agent framework) |
| Vector Store | ChromaDB (local, persistent) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (runs locally) |
| Database | MongoDB via Motor (async driver) |
| LLM | Configurable — `demo` mode (deterministic, no API key) or `openai` mode |

> **Why Semantic Kernel instead of Microsoft Agent Framework?**
> Microsoft Agent Framework is not publicly available as a standalone pip package. Semantic Kernel is Microsoft's production-ready, open-source Python agent and orchestration framework (`semantic-kernel` on PyPI). It provides kernel functions, plugin-based agent coordination, and planner-executor patterns identical in architecture to what the spec requires. The choice is documented here and in `docs/architecture.md`.

---

## Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Docker Desktop (for MongoDB) — or a local MongoDB 7 instance
- Internet connection for first run (downloads `all-MiniLM-L6-v2` from HuggingFace, ~90 MB)

---

## Setup

### 1. Clone / open the project
```bash
cd museum-exhibit-guide
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env if needed. Defaults work for demo mode with Docker MongoDB.
# LLM_MODE=demo  ← no API key needed
```

### 3. Start MongoDB
```bash
docker compose up -d
```

### 4. Backend setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Seed database
```bash
python scripts/seed_database.py
```

### 6. Ingest RAG catalogue (builds ChromaDB index)
```bash
python scripts/ingest_catalogue.py
```

### 7. Start backend server
```bash
uvicorn app.main:app --reload --port 8000
```
Backend available at: http://localhost:8000
API docs: http://localhost:8000/api/docs

### 8. Frontend setup (new terminal)
```bash
cd frontend
npm install
npm run dev
```
Frontend available at: http://localhost:5173

---

## Running Tests

```bash
cd backend
source .venv/bin/activate
pytest -v
```

Expected: **50 tests, 0 failures**

Test files:
- `tests/test_tools.py` — walking distance, opening hours, crowd status
- `tests/test_memory.py` — visitor memory persistence
- `tests/test_rag.py` — chunking, ingestion, retrieval
- `tests/test_agents.py` — all five agents
- `tests/test_orchestration.py` — planner-executor workflow
- `tests/test_crowd_replanning.py` — crowd-aware replanning
- `tests/test_evaluation.py` — evaluation metrics

---

## Running Evaluation

```bash
cd backend
source .venv/bin/activate
python scripts/run_evaluation.py
```

Generates:
- `evaluation_reports/report_<timestamp>.json` — machine-readable
- `evaluation_reports/report_<timestamp>.md` — human-readable table

**Actual results (last run):**
| Metric | Value |
|---|---|
| Time Budget Fit Rate | 37.5% |
| Avg Interest Coverage | 95.8% |
| Avg Exhibits per Route | 4.0 |
| Avg Walking Time | 3.4 min |
| Accessibility Compliance | 100.0% |

---

## Demo Mode

The application runs fully without an LLM API key. Set `LLM_MODE=demo` in `.env` (the default). Commentary is generated deterministically from retrieved evidence chunks.

To use OpenAI:
```env
LLM_MODE=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

---

## Re-indexing RAG

After adding new exhibits or curator notes:
```bash
python scripts/ingest_catalogue.py --force
# or via API:
curl -X POST http://localhost:8000/api/admin/reindex
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_MODE` | `demo` | `demo` or `openai` |
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection |
| `MONGODB_DB_NAME` | `museum_guide` | Database name |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | ChromaDB storage path |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `OPENAI_API_KEY` | — | Only needed if `LLM_MODE=openai` |
| `FRONTEND_URL` | `http://localhost:5173` | CORS origin |

---

## Project Structure

```
museum-exhibit-guide/
├── README.md
├── PROJECT_SPEC.md
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── architecture.md
│   ├── agent-workflow.md
│   ├── rag-design.md
│   ├── shared-memory.md
│   ├── evaluation-methodology.md
│   ├── demo-script.md
│   └── api-overview.md
├── backend/
│   ├── app/
│   │   ├── agents/          ← 5 separate agent modules + contracts
│   │   ├── orchestration/   ← planner_executor, workflow_state, framework_adapter
│   │   ├── rag/             ← chunking, embeddings, ingestion, retriever, vector_store
│   │   ├── memory/          ← visitor_memory service
│   │   ├── tools/           ← walking_distance, opening_hours, crowd_status
│   │   ├── models/          ← Pydantic models (visitor, exhibit, visit, evaluation)
│   │   ├── services/        ← visit_service, evaluation_service
│   │   ├── api/routes/      ← FastAPI routes for all endpoints
│   │   ├── core/            ← config, logging, exceptions
│   │   └── data/            ← exhibits.json, galleries.json, curator_notes/
│   ├── scripts/             ← seed_database, ingest_catalogue, run_evaluation
│   └── tests/               ← 50 tests across 7 test files
└── frontend/
    └── src/
        ├── pages/           ← Home, PlanVisit, VisitGuide, CrowdControl, Memory, Evaluation, About
        ├── components/      ← Navbar, LoadingSpinner, ErrorMessage
        ├── api/             ← typed Axios client
        ├── types/           ← TypeScript interfaces
        └── styles/          ← Tailwind CSS
```
