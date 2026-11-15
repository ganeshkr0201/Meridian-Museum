# Demo Script — 3–5 Minute College Demonstration

**Project:** Q26 — Meridian Museum Personalised Exhibit Guide
**Group:** 12317780 Ganesh Kumar, 12320064 Saurav

---

## Setup Before Demo (5 min before)

```bash
# Terminal 1 — Backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open browser: http://localhost:5173

---

## Script

### Part 1 — Introduction (30 sec)
*"This is the Meridian Museum Personalised Exhibit Guide. It uses a five-agent AI pipeline — not a single chatbot — to generate a custom visit route with grounded commentary for each visitor. I'll show you a plan, the agent trace, crowd-aware replanning, and the evaluation dashboard."*

---

### Part 2 — Plan a Visit (60 sec)

1. Click **"Plan My Visit"**
2. Enter name: **"Demo Visitor"**
3. Select interests: **ancient history**, **science**, **art**
4. Set time budget: **60 minutes**
5. Leave accessibility as **none**, commentary **medium**
6. Click **"Generate My Visit Guide →"**

*While loading:*
*"The orchestrator is running five agents in sequence. First the Visitor Profile Agent normalises input and writes to shared memory. Then the Exhibit Retrieval Agent queries our ChromaDB vector store — 61 chunks from 13 curator notes and 12 catalogue entries. The Route Planner uses a seeded museum graph with Dijkstra's algorithm for walking distances..."*

---

### Part 3 — Explore the Guide (60 sec)

The guide loads with the route timeline.

1. Point to **Stop 1**: *"Each stop shows visit time, walking time from the previous gallery, accessibility status, and opening hours."*
2. Expand commentary: *"This commentary was generated from retrieved evidence — not invented. You can see the curator note source reference at the bottom."*
3. Click the **Trace** tab: *"Here you can see all five agents: Visitor Profile, Exhibit Retrieval, Route Planner, Commentary Writer, Guide Manager — each with start time, duration, input and output summary. This is real execution, not a mock."*
4. Click **Skipped** tab: *"Exhibits that didn't make the route are listed here with a reason code — time budget, opening hours, or accessibility."*

---

### Part 4 — Crowd-Aware Replanning (60 sec)

1. Click **"Mark Gallery Busy & Replan"** button (bottom of route tab)
2. Navigate to **Crowd Control** page
3. Find **Ancient Civilisations Gallery (G01)**, click **busy**
4. Click **"🔄 Replan Avoiding This Gallery"**

*"The system re-runs agents 2–5 with this gallery excluded from the candidate set. Already-visited stops are preserved. Remaining time is recalculated. Watch the route change..."*

5. The updated route appears with an explanation banner.
*"You can see which stop was removed, why, and what replaced it. The replan version counter incremented from 0 to 1."*

---

### Part 5 — Evaluation Dashboard (45 sec)

1. Navigate to **Evaluation**
2. Click **"▶ Run Evaluation"**

*"This runs the full planning pipeline for all eight seeded visitor profiles — ancient history enthusiast, wheelchair user, broad interests, 30-minute time constraint, and so on."*

3. Results load showing the metrics table.
*"Time Budget Fit Rate is 37.5% — honest, because some tight budgets produce routes slightly over. Interest Coverage averages 95.8% — most profiles get all their interests represented. Accessibility compliance is 100% — wheelchair and step-free profiles only receive accessible stops."*

---

### Part 6 — About / Architecture (30 sec)

1. Navigate to **About**
2. Show architecture diagram in the page

*"Each agent is a separate Python module with typed Pydantic input/output contracts. The orchestrator uses Semantic Kernel — Microsoft's open-source agent framework — to coordinate them. Shared memory in MongoDB persists across sessions. The RAG pipeline uses sentence-transformers locally, no API key required."*

---

## Closing Statement

*"The system runs entirely locally in demo mode — no paid API keys needed. The evaluation generates real metrics from actual routes. All five agents have observable execution traces. Thank you."*

---

## Backup Commands

```bash
# If backend is not responding:
uvicorn app.main:app --reload --port 8000

# If ChromaDB is empty:
python scripts/ingest_catalogue.py --force

# Run evaluation manually:
python scripts/run_evaluation.py

# Check health:
curl http://localhost:8000/api/health
```
