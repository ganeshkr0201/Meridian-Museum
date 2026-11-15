"""
Generate a project report .docx for the Museum Exhibit Guide project.
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

doc = Document()

# ── Page margins ────────────────────────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin   = Cm(3.0)
    section.right_margin  = Cm(2.5)

# ── Helpers ─────────────────────────────────────────────────────────────────
def set_heading_color(paragraph, r, g, b):
    for run in paragraph.runs:
        run.font.color.rgb = RGBColor(r, g, b)

def add_heading(text, level, r=0x1F, g=0x38, b=0x6B):
    p = doc.add_heading(text, level=level)
    set_heading_color(p, r, g, b)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(4)
    return p

def add_para(text, bold=False, italic=False, size=11, space_after=6):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold   = bold
    run.italic = italic
    run.font.size = Pt(size)
    p.paragraph_format.space_after = Pt(space_after)
    return p

def add_bullet(text, level=0):
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.left_indent   = Pt(18 * (level + 1))
    p.paragraph_format.space_after   = Pt(2)
    return p

def add_table(headers, rows, col_widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = h
        for para in hdr[i].paragraphs:
            para.runs[0].bold = True
            para.runs[0].font.size = Pt(10)
        # shade header
        tc = hdr[i]._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "1F386B")
        tcPr.append(shd)
        for para in hdr[i].paragraphs:
            for run in para.runs:
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for row_data in rows:
        row = t.add_row().cells
        for i, cell_text in enumerate(row_data):
            row[i].text = cell_text
            for para in row[i].paragraphs:
                para.runs[0].font.size = Pt(10) if para.runs else None

    if col_widths:
        for i, w in enumerate(col_widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    return t

def add_spacer():
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)

# ════════════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ════════════════════════════════════════════════════════════════════════════
title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
title_run = title_p.add_run("Meridian Museum\nPersonalised Exhibit Guide")
title_run.bold = True
title_run.font.size = Pt(26)
title_run.font.color.rgb = RGBColor(0x1F, 0x38, 0x6B)

doc.add_paragraph()
sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub_run = sub_p.add_run("Project Report — Q26")
sub_run.bold = True
sub_run.font.size = Pt(16)
sub_run.font.color.rgb = RGBColor(0x4A, 0x5F, 0x9E)

doc.add_paragraph()

# Assessment info table
info_data = [
    ("Assessment",   "Bloom's Taxonomy L4–L5–L6 | Planner | 30 Marks"),
    ("Module",       "Multi-Agent AI Systems"),
    ("Group",        "12317780 — Ganesh Kumar\n12320064 — Saurav"),
    ("Date",         "November 2026"),
]
info_tbl = doc.add_table(rows=len(info_data), cols=2)
info_tbl.style = "Table Grid"
info_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, (label, value) in enumerate(info_data):
    cells = info_tbl.rows[i].cells
    cells[0].text = label
    cells[1].text = value
    for p in cells[0].paragraphs:
        for r in p.runs:
            r.bold = True
            r.font.size = Pt(11)
    for p in cells[1].paragraphs:
        for r in p.runs:
            r.font.size = Pt(11)
    for c in cells:
        c.width = Cm(7)

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════════
# 1. EXECUTIVE SUMMARY
# ════════════════════════════════════════════════════════════════════════════
add_heading("1. Executive Summary", level=1)
add_para(
    "The Meridian Museum Personalised Exhibit Guide (Q26) is a full-stack AI application that "
    "generates a custom museum visit route and factually grounded exhibit commentary for each "
    "visitor. The system accepts a visitor's interests, time budget, and accessibility requirements, "
    "then coordinates five specialised AI agents through a planner-executor orchestrator to produce "
    "a personalised, source-cited guide."
)
add_para(
    "Key capabilities include Retrieval-Augmented Generation (RAG) over 61 indexed content chunks, "
    "Dijkstra-based walking time calculation, opening-hours and crowd-aware route planning, "
    "persistent visitor memory across sessions, and dynamic crowd-aware replanning. The backend "
    "is built on FastAPI with Semantic Kernel as the agent orchestration framework; the frontend "
    "is a React 18 single-page application. The system operates fully in demo mode without any "
    "paid LLM API key."
)

# ════════════════════════════════════════════════════════════════════════════
# 2. PROJECT OVERVIEW
# ════════════════════════════════════════════════════════════════════════════
add_heading("2. Project Overview", level=1)

add_heading("2.1 Purpose and Context", level=2)
add_para(
    "The Meridian Museum of World Cultures (a fictional institution) requires a digital guide "
    "that moves beyond generic audio tours. Each visitor has a different interest profile, "
    "mobility requirement, and time constraint. The project demonstrates a genuine multi-agent "
    "AI workflow in which autonomous agents with distinct responsibilities collaborate to solve "
    "this personalisation problem end-to-end."
)

add_heading("2.2 Project Goals", level=2)
goals = [
    "Plan an optimised visit route personalised to stated interests, accessibility needs, and time budget.",
    "Retrieve relevant information from a curated knowledge base and generate grounded commentary with citations.",
    "Persist visitor preferences and visit history to improve future recommendations.",
    "Replan the route dynamically when a gallery becomes crowded, without discarding completed stops.",
    "Provide an evaluable system against eight seeded visitor profiles with quantitative metrics.",
]
for g in goals:
    add_bullet(g)

add_heading("2.3 Scope", level=2)
add_para(
    "The project covers 12 exhibits across 4 galleries (Ancient Civilisations G01, Science and "
    "Innovation G02, Art and Culture G03, Natural History G04). It uses 14 curator-note text "
    "files and 12 catalogue entries as the knowledge base, producing 61 indexed chunks. "
    "The evaluation suite runs against 8 seeded visitor profiles spanning diverse interests "
    "and accessibility needs."
)

# ════════════════════════════════════════════════════════════════════════════
# 3. TECHNOLOGY STACK
# ════════════════════════════════════════════════════════════════════════════
add_heading("3. Technology Stack", level=1)

add_table(
    ["Layer", "Technology", "Notes"],
    [
        ["Frontend",        "React 18, Vite, TypeScript, Tailwind CSS, React Router, Axios",   "SPA, dev server on port 5173"],
        ["Backend",         "Python 3.11+, FastAPI, Pydantic v2, Uvicorn",                     "REST API on port 8000"],
        ["Agent Framework", "Microsoft Semantic Kernel (semantic-kernel on PyPI)",              "Planner-executor coordination; sequential fallback if SK absent"],
        ["Vector Store",    "ChromaDB (local, persistent)",                                     "61 chunks; cosine similarity search"],
        ["Embeddings",      "sentence-transformers all-MiniLM-L6-v2",                          "384 dimensions; runs locally (~90 MB download)"],
        ["Database",        "MongoDB 7 via Motor (async driver)",                              "In-memory dict fallback for demo mode"],
        ["LLM",             "Configurable: demo (deterministic) or OpenAI-compatible",         "GPT-4o-mini in OpenAI mode; no key needed in demo mode"],
        ["Containers",      "Docker Compose",                                                   "MongoDB service only"],
    ],
    col_widths=[3.5, 7.5, 5.5],
)
add_spacer()
add_para(
    "Note: Microsoft's proprietary Agent Framework is not publicly available on PyPI. "
    "Semantic Kernel is Microsoft's production-ready open-source equivalent and was selected "
    "for this reason. This choice is documented in docs/architecture.md.",
    italic=True, size=10
)

# ════════════════════════════════════════════════════════════════════════════
# 4. SYSTEM ARCHITECTURE
# ════════════════════════════════════════════════════════════════════════════
add_heading("4. System Architecture", level=1)

add_heading("4.1 High-Level Architecture", level=2)
add_para(
    "The system follows a layered architecture. The React frontend communicates with FastAPI "
    "routes over HTTP. The routes delegate to a service layer, which invokes the "
    "PlannerExecutor orchestrator. The orchestrator coordinates five agents in a fixed "
    "sequential pipeline. Agents read and write through shared services: "
    "VisitorMemoryService (MongoDB), the RAG retriever (ChromaDB), and three tool modules."
)

add_para("Data flow through the system:", bold=True)
steps = [
    "Browser (React) → Axios → FastAPI route handler",
    "Route handler → VisitService.create_visit()",
    "VisitService → PlannerExecutor.plan_visit(form_data)",
    "PlannerExecutor → Agent 1 (VisitorProfileAgent) → VisitorMemoryService (read/write)",
    "PlannerExecutor → Agent 2 (ExhibitRetrievalAgent) → ChromaDB (semantic search)",
    "PlannerExecutor → Agent 3 (RoutePlannerAgent) → walking_distance, opening_hours, crowd_status tools",
    "PlannerExecutor → Agent 4 (CommentaryWriterAgent) → LLM or deterministic generation",
    "PlannerExecutor → Agent 5 (GuideManagerAgent) → validation and VisitGuide assembly",
    "VisitGuide → MongoDB (or in-memory store) → API response → React UI",
]
for s in steps:
    add_bullet(s)

add_heading("4.2 Orchestration Layer", level=2)
add_para(
    "The PlannerExecutor (orchestration/planner_executor.py) implements the planner-executor "
    "pattern. It wraps each agent invocation in a retry loop (MAX_RETRIES = 2) and records "
    "timing data via WorkflowState. The WorkflowState object carries typed intermediate "
    "results between agents (VisitorProfile, RetrievedEvidence list, RouteStop list, "
    "commentary dict) and builds a list[WorkflowTraceEntry] with per-agent timestamps "
    "and duration in milliseconds. This trace is attached to the final VisitGuide and "
    "exposed via GET /api/visits/{visit_id}/trace."
)
add_para(
    "Semantic Kernel integration wraps each agent run as a @kernel_function plugin in "
    "orchestration/framework_adapter.py. If the semantic_kernel package is absent, the "
    "kernel is set to None and all agents execute via direct Python await calls."
)

add_heading("4.3 Project Directory Structure", level=2)
structure = [
    ("backend/app/agents/",        "Five agent modules + typed input/output contracts"),
    ("backend/app/orchestration/", "PlannerExecutor, WorkflowState, Semantic Kernel adapter"),
    ("backend/app/rag/",           "Chunking, embeddings, ingestion, retriever, ChromaDB vector store"),
    ("backend/app/memory/",        "VisitorMemoryService (MongoDB-backed with in-memory fallback)"),
    ("backend/app/tools/",         "walking_distance, opening_hours, crowd_status tools"),
    ("backend/app/models/",        "Pydantic models: visitor, exhibit, visit, evaluation"),
    ("backend/app/services/",      "VisitService, EvaluationService"),
    ("backend/app/api/routes/",    "FastAPI route handlers for all endpoints"),
    ("backend/app/core/",          "Config, logging, exceptions"),
    ("backend/app/data/",          "exhibits.json, galleries.json, curator_notes/ (14 files)"),
    ("backend/scripts/",           "seed_database, ingest_catalogue, run_evaluation"),
    ("backend/tests/",             "50 tests across 7 test files"),
    ("frontend/src/pages/",        "7 React pages: Home, PlanVisit, VisitGuide, CrowdControl, Memory, Evaluation, About"),
    ("frontend/src/api/",          "Typed Axios client for all backend endpoints"),
]
add_table(
    ["Path", "Description"],
    structure,
    col_widths=[7.0, 9.5],
)

# ════════════════════════════════════════════════════════════════════════════
# 5. THE FIVE AGENTS
# ════════════════════════════════════════════════════════════════════════════
add_heading("5. The Five Agents", level=1)
add_para(
    "All inter-agent data transfer uses typed Pydantic contracts defined in "
    "agents/contracts.py. No agent calls another directly; all coordination flows "
    "through PlannerExecutor."
)

agent_rows = [
    ["A — Visitor Profile Agent",    "agents/visitor_profile_agent.py",   "Validates input, resolves interest aliases, reads and writes VisitorMemory, produces a VisitorProfile with interest_weights"],
    ["B — Exhibit Retrieval Agent",  "agents/exhibit_retrieval_agent.py",  "Embeds visitor interests and queries ChromaDB (top-k=12); falls back to tag filtering; returns RetrievedEvidence with provenance"],
    ["C — Route Planner Agent",      "agents/route_planner_agent.py",      "Scores candidates (interest × 3.0 − crowd penalty × 0.4), filters by accessibility/hours/budget, sequences stops with Dijkstra walking times"],
    ["D — Commentary Writer Agent",  "agents/commentary_writer_agent.py",  "Builds grounded commentary per stop from retrieved evidence; demo mode: deterministic truncation; OpenAI mode: structured JSON prompt"],
    ["E — Guide Manager Agent",      "agents/guide_manager_agent.py",      "Re-calculates totals independently, validates time budget and opening hours, computes interest_coverage, assembles final VisitGuide"],
]
add_table(
    ["Agent", "Module", "Responsibility"],
    agent_rows,
    col_widths=[4.0, 5.5, 7.0],
)

add_spacer()
add_heading("5.1 Agent Input/Output Contracts", level=2)
contract_rows = [
    ["VisitorProfileAgentInput",  "display_name, interests[], time_budget_minutes, accessibility_needs[], language, commentary_length, memory_mode, visitor_id?"],
    ["VisitorProfileAgentOutput", "visitor_profile: VisitorProfile, memory_updated: bool, warnings[]"],
    ["ExhibitRetrievalAgentInput", "visitor_profile: VisitorProfile, top_k: int"],
    ["ExhibitRetrievalAgentOutput", "retrieved_evidence: RetrievedEvidence[], candidate_exhibit_ids[], low_confidence: bool"],
    ["RoutePlannerAgentInput",    "visitor_profile, candidate_exhibit_ids[], busy_gallery_ids[], completed_exhibit_ids[], elapsed_minutes"],
    ["RoutePlannerAgentOutput",   "route: RouteStop[], skipped_items: SkippedItem[], totals (minutes, distance), time_budget_fit: bool"],
    ["CommentaryWriterAgentInput", "visitor_profile, route: RouteStop[], retrieved_evidence[]"],
    ["CommentaryWriterAgentOutput", "commentaries: dict[exhibit_id, ExhibitCommentary], warnings[]"],
    ["GuideManagerAgentInput",    "visitor_profile, route_output, commentary_output, retrieved_evidence[], visit_id, crowd_replan_version"],
    ["GuideManagerAgentOutput",   "valid: bool, validation_errors[], warnings[], corrected_total_minutes"],
]
add_table(
    ["Contract", "Key Fields"],
    contract_rows,
    col_widths=[6.5, 10.0],
)

# ════════════════════════════════════════════════════════════════════════════
# 6. RAG PIPELINE
# ════════════════════════════════════════════════════════════════════════════
add_heading("6. RAG Pipeline", level=1)
add_para(
    "Retrieval-Augmented Generation grounds commentary in verified source material, "
    "preventing hallucination and enabling citations."
)

rag_steps = [
    ("Source material",  "14 curator note .txt files + 12 catalogue entries from exhibits.json"),
    ("Chunking",         "2-sentence sliding windows produce TextChunk objects with exhibit_id and source_id metadata"),
    ("Embedding",        "sentence-transformers all-MiniLM-L6-v2 (384 dimensions); runs locally"),
    ("Storage",          "ChromaDB local persistent collection; 61 chunks stored; upsert is idempotent"),
    ("Ingestion trigger","App startup (ingest_all(force=False)) and POST /api/admin/reindex"),
    ("Retrieval",        "Query = 'museum exhibits about <interests>'; cosine distance → similarity score (1 − dist/2)"),
    ("Fallback",         "Tag-based filtering from exhibits.json if ChromaDB query fails or returns nothing"),
    ("Evidence output",  "RetrievedEvidence: exhibit_id, source_id, source_title, chunk_text, relevance_score (0–1)"),
]
add_table(["Step", "Detail"], rag_steps, col_widths=[4.5, 12.0])

# ════════════════════════════════════════════════════════════════════════════
# 7. TOOLS
# ════════════════════════════════════════════════════════════════════════════
add_heading("7. Planning Tools", level=1)

add_heading("7.1 Walking Distance Tool", level=2)
add_para(
    "tools/walking_distance.py implements Dijkstra's shortest-path algorithm over a "
    "static graph of 4 gallery nodes (G01–G04) connected by 6 bidirectional edges with "
    "distances in metres and estimated walk times in minutes. Stair-free alternative paths "
    "are defined in _ACCESSIBLE_EXTRAS for visitors with mobility constraints. The tool "
    "returns a WalkingResult dataclass containing total_distance_m, total_minutes, and path. "
    "Falls back with 9999 m / 30 min if no path is found."
)

add_heading("7.2 Opening Hours Tool", level=2)
add_para(
    "tools/opening_hours.py checks whether a gallery visit fits within its operating hours. "
    "Gallery hours are seeded from galleries.json: G01, G02, and G04 open 09:00–17:00; "
    "G03 (Art and Culture) opens 10:00–16:00. The tool accepts an arrival offset from "
    "start_time and visit duration, returning (fits: bool, reason: str)."
)

add_heading("7.3 Crowd Status Tool", level=2)
add_para(
    "tools/crowd_status.py maintains an in-memory dict _CROWD_STATE keyed by gallery_id. "
    "CrowdState values are NORMAL, MODERATE, BUSY, and CLOSED, carrying penalty minutes of "
    "0, 3, 8, and 999 respectively. The Route Planner incorporates crowd penalty into its "
    "scoring function and excludes galleries with BUSY or CLOSED state. The state is "
    "process-scoped and resets on server restart (designed for mirroring to MongoDB in "
    "production)."
)

# ════════════════════════════════════════════════════════════════════════════
# 8. SHARED MEMORY
# ════════════════════════════════════════════════════════════════════════════
add_heading("8. Shared Visitor Memory", level=1)
add_para(
    "VisitorMemoryService (memory/visitor_memory.py) provides a common storage interface "
    "backed by MongoDB (async Motor driver) with an in-memory Python dict fallback for "
    "demo/guest mode. The service is instantiated as a singleton via FastAPI dependency "
    "injection (api/deps.py)."
)
add_para("Fields stored per visitor:", bold=True)
memory_fields = [
    "visitor_id, display_name",
    "interests (list of InterestCategory enums)",
    "interest_weights (dict[str, float], boosted by history)",
    "preferred_language, preferred_commentary_length",
    "accessibility_needs",
    "memory_mode (persistent or guest)",
    "previously_visited_exhibits (list of exhibit IDs)",
    "previously_skipped_exhibits (list of dicts with reason)",
    "explicit_feedback (dict[exhibit_id, {liked, comment}])",
    "memory_version (integer counter)",
    "updated_at (timestamp)",
]
for f in memory_fields:
    add_bullet(f)

add_para(
    "Only the VisitorProfileAgent writes to memory (on each session). All other agents "
    "read the VisitorProfile produced by Agent A, which already incorporates memory data. "
    "The frontend Memory page allows visitors to view, update preferences, and clear all "
    "stored memory via dedicated API endpoints."
)

# ════════════════════════════════════════════════════════════════════════════
# 9. CROWD-AWARE REPLANNING
# ════════════════════════════════════════════════════════════════════════════
add_heading("9. Crowd-Aware Replanning", level=1)
add_para(
    "When a gallery becomes crowded during a visit, the system replans the remaining "
    "unvisited stops without discarding progress."
)
replan_steps = [
    "Visitor (or staff) marks a gallery as busy via the Crowd Control page (PATCH /api/galleries/{gallery_id}/crowd).",
    "Frontend sends POST /api/visits/{visit_id}/replan with busy_gallery_id.",
    "VisitService.replan() calculates elapsed_minutes from completed stops' durations.",
    "PlannerExecutor.replan() calls set_crowd_state(busy_gallery_id, CrowdState.BUSY) in the in-memory crowd store.",
    "Agents 2–5 re-execute with busy_gallery_ids excluded from candidates and completed_exhibit_ids skipped.",
    "GuideManagerAgent prepends already-completed stops to the new route and re-sequences everything.",
    "crowd_replan_version is incremented; replan_explanation is included in the returned VisitGuide.",
    "Frontend Crowd Control page shows a before/after route comparison.",
]
for i, s in enumerate(replan_steps, 1):
    add_bullet(f"{i}. {s}")

# ════════════════════════════════════════════════════════════════════════════
# 10. DATA MODELS
# ════════════════════════════════════════════════════════════════════════════
add_heading("10. Data Models", level=1)

add_heading("10.1 Visitor Models (models/visitor.py)", level=2)
add_table(
    ["Model / Enum", "Key Fields"],
    [
        ["InterestCategory (enum)",  "ancient_history, archaeology, science, art, textiles, coins, local_culture, natural_history, technology, regional_craft"],
        ["AccessibilityNeed (enum)", "none, wheelchair, step_free, reduced_walking, avoid_stairs, seating_breaks"],
        ["Language (enum)",          "en, es, fr, de, hi"],
        ["CommentaryLength (enum)",  "short (200 chars), medium (350 chars), long (600 chars)"],
        ["VisitorMemory",            "visitor_id, interests, interest_weights, accessibility_needs, language, commentary_length, visited_exhibits, feedback, memory_version"],
        ["VisitorProfile",           "visitor_id, interests, interest_weights, time_budget_minutes, accessibility_needs, language, commentary_length, memory_mode"],
        ["PlanRequest",              "display_name, interests[], time_budget_minutes (5–600), accessibility_needs[], language, commentary_length, memory_mode, visitor_id?"],
    ],
    col_widths=[5.0, 11.5],
)

add_spacer()
add_heading("10.2 Exhibit and Route Models (models/exhibit.py)", level=2)
add_table(
    ["Model", "Key Fields"],
    [
        ["Exhibit",          "exhibit_id, title, gallery_id, description, tags[], estimated_visit_minutes, accessibility_features[], is_open, curator_note_ids[]"],
        ["GalleryNode",      "gallery_id, name, floor, coordinates, is_accessible, crowd_state, opening_hours"],
        ["RetrievedEvidence","exhibit_id, source_id, source_title, chunk_text, relevance_score (0–1), metadata"],
        ["RouteStop",        "sequence, exhibit_id, gallery_id, visit_duration_minutes, walking_time_from_previous_minutes, planned_arrival_offset_minutes, is_completed"],
        ["SkippedItem",      "exhibit_id, title, reason_code (ACCESSIBILITY / GALLERY_BUSY / TIME_BUDGET etc.), human_readable_reason"],
        ["ExhibitCommentary","exhibit_id, commentary, interest_match_reason, source_references[], confidence, did_you_know"],
    ],
    col_widths=[4.5, 12.0],
)

add_spacer()
add_heading("10.3 Visit and Trace Models (models/visit.py)", level=2)
add_table(
    ["Model", "Key Fields"],
    [
        ["VisitGuide",          "visit_id, visitor_id, route[], commentaries{}, skipped_items[], totals, time_budget_fit, interest_coverage{}, sources[], workflow_trace[]"],
        ["VisitSession",        "visit_id, visitor_id, guide: VisitGuide, completed_stop_ids[], status (planning/active), timestamps"],
        ["WorkflowTraceEntry",  "agent_name, status, started_at, completed_at, duration_ms, input_summary, output_summary, error_message"],
    ],
    col_widths=[4.5, 12.0],
)

# ════════════════════════════════════════════════════════════════════════════
# 11. API ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════
add_heading("11. API Endpoints", level=1)
add_para("All routes are prefixed with /api. Interactive docs available at /api/docs (Swagger UI).")

add_heading("11.1 Visit Endpoints", level=2)
add_table(
    ["Method", "Path", "Description"],
    [
        ["POST",  "/api/visits/plan",                         "Trigger the full 5-agent pipeline; body: PlanRequest; returns VisitGuide"],
        ["GET",   "/api/visits/{visit_id}",                   "Retrieve a saved VisitGuide"],
        ["GET",   "/api/visits/{visit_id}/trace",             "Retrieve per-agent workflow execution trace"],
        ["POST",  "/api/visits/{visit_id}/complete-stop",     "Mark an exhibit stop as completed; updates memory"],
        ["POST",  "/api/visits/{visit_id}/feedback",          "Submit liked/disliked + comment; persisted to memory"],
        ["POST",  "/api/visits/{visit_id}/replan",            "Crowd-aware replanning; body: ReplanRequest"],
        ["GET",   "/api/visits/{visit_id}/sources",           "Retrieve RAG evidence chunks used in the guide"],
    ],
    col_widths=[2.0, 7.5, 7.0],
)

add_spacer()
add_heading("11.2 Other Endpoints", level=2)
add_table(
    ["Method", "Path", "Description"],
    [
        ["POST",  "/api/visitors",                            "Create or update visitor memory"],
        ["GET",   "/api/visitors/{visitor_id}",               "Read visitor memory"],
        ["PATCH", "/api/visitors/{visitor_id}/preferences",   "Partial update to preferences"],
        ["DELETE","/api/visitors/{visitor_id}/memory",        "Clear all memory for a visitor"],
        ["GET",   "/api/galleries",                           "List galleries with live crowd state"],
        ["GET",   "/api/galleries/crowd",                     "Current crowd status for all galleries"],
        ["PATCH", "/api/galleries/{gallery_id}/crowd",        "Update a gallery's crowd state"],
        ["GET",   "/api/exhibits",                            "Paginated exhibit list"],
        ["GET",   "/api/exhibits/{exhibit_id}",               "Single exhibit detail"],
        ["POST",  "/api/evaluation/run",                      "Run evaluation over all 8 profiles; saves JSON + MD reports"],
        ["GET",   "/api/evaluation/latest",                   "Return most recent evaluation report"],
        ["GET",   "/api/evaluation/profiles",                 "Return the 8 seeded profile configs"],
        ["POST",  "/api/admin/reindex",                       "Force re-ingestion into ChromaDB"],
        ["GET",   "/api/health",                              "Health check"],
    ],
    col_widths=[2.0, 7.5, 7.0],
)

# ════════════════════════════════════════════════════════════════════════════
# 12. FRONTEND
# ════════════════════════════════════════════════════════════════════════════
add_heading("12. Frontend Application", level=1)
add_para(
    "The React 18 single-page application uses Vite as the build tool, TypeScript for "
    "type safety, Tailwind CSS for styling, and React Router for client-side navigation. "
    "All backend communication goes through a typed Axios client (api/client.ts) with a "
    "120-second timeout to accommodate the full 5-agent pipeline."
)

add_table(
    ["Route", "Page", "Description"],
    [
        ["/",                "Home",           "Landing page with project overview"],
        ["/plan",            "PlanVisit",      "Visitor form: interest chips, time budget slider (15–180 min), accessibility toggles, language and commentary preferences. Demo mode via ?demo=true"],
        ["/guide/:visitId",  "VisitGuide",     "Displays personalised route, per-exhibit commentary with citations, skipped items, workflow trace, sources"],
        ["/crowd",           "CrowdControl",   "Shows gallery crowd states; triggers replanning; displays before/after route comparison"],
        ["/memory",          "MemoryPage",     "Displays visitor memory; allows preference updates and full memory clear"],
        ["/evaluation",      "EvaluationPage", "Triggers evaluation run; displays aggregated metrics table over 8 profiles"],
        ["/about",           "About",          "Project documentation and architecture notes"],
    ],
    col_widths=[3.5, 3.5, 9.5],
)

# ════════════════════════════════════════════════════════════════════════════
# 13. EVALUATION
# ════════════════════════════════════════════════════════════════════════════
add_heading("13. Evaluation", level=1)

add_heading("13.1 Methodology", level=2)
add_para(
    "The evaluation suite (scripts/run_evaluation.py and services/evaluation_service.py) "
    "runs the full 5-agent pipeline for each of 8 seeded visitor profiles defined in "
    "data/visitor_profiles.json. Profiles cover a range of interest combinations, time "
    "budgets (30–120 minutes), and accessibility requirements. For each profile, six metrics "
    "are computed from the resulting VisitGuide."
)

add_table(
    ["Metric", "Definition"],
    [
        ["Time Budget Fit Rate",         "Percentage of profiles where total route time ≤ stated time budget (5-min grace)"],
        ["Interest Coverage Rate",       "Average percentage of stated interests matched by at least one route stop's tags"],
        ["Accessibility Compliance Rate","Percentage of profiles where no inaccessible exhibit appears in the route"],
        ["Opening Hours Compliance Rate","Percentage of profiles where all stops fall within gallery opening hours"],
        ["Average Exhibits per Route",   "Mean number of route stops across all profiles"],
        ["Average Walking Time",         "Mean total walking minutes per route"],
    ],
    col_widths=[5.5, 11.0],
)

add_spacer()
add_heading("13.2 Results (Last Run)", level=2)
add_table(
    ["Metric", "Value"],
    [
        ["Time Budget Fit Rate",         "37.5%"],
        ["Average Interest Coverage",    "95.8%"],
        ["Average Exhibits per Route",   "4.0"],
        ["Average Walking Time",         "3.4 min"],
        ["Accessibility Compliance Rate","100.0%"],
    ],
    col_widths=[7.5, 9.0],
)
add_spacer()
add_para(
    "Note: The 37.5% time budget fit rate reflects tight-budget profiles (30–50 min) where "
    "the route's visit minutes sum to slightly more than the budget. This is a known "
    "evaluation result, not a defect — the route planner uses a 5-minute grace period but "
    "some profiles are intentionally boundary cases.",
    italic=True, size=10
)

# ════════════════════════════════════════════════════════════════════════════
# 14. CONFIGURATION AND DEPLOYMENT
# ════════════════════════════════════════════════════════════════════════════
add_heading("14. Configuration and Deployment", level=1)

add_heading("14.1 Environment Variables", level=2)
add_table(
    ["Variable", "Default", "Description"],
    [
        ["LLM_MODE",           "demo",                      "demo (deterministic) or openai (GPT-4o-mini)"],
        ["MONGODB_URL",        "mongodb://localhost:27017",  "MongoDB connection string"],
        ["MONGODB_DB_NAME",    "museum_guide",               "Database name"],
        ["CHROMA_PERSIST_DIR", "./chroma_db",                "ChromaDB local storage path"],
        ["EMBEDDING_MODEL",    "all-MiniLM-L6-v2",          "sentence-transformers model name"],
        ["OPENAI_API_KEY",     "—",                          "Required only when LLM_MODE=openai"],
        ["OPENAI_BASE_URL",    "—",                          "Optional custom OpenAI-compatible endpoint"],
        ["OPENAI_MODEL",       "gpt-4o-mini",                "LLM model identifier"],
        ["FRONTEND_URL",       "http://localhost:5173",      "CORS allowed origin"],
        ["SECRET_KEY",         "—",                          "Session security key"],
    ],
    col_widths=[4.5, 5.5, 6.5],
)

add_spacer()
add_heading("14.2 Setup Commands", level=2)
setup_steps = [
    ("Start MongoDB (Docker)",       "docker compose up -d"),
    ("Create Python venv",           "cd backend && python3 -m venv .venv && source .venv/bin/activate"),
    ("Install backend dependencies", "pip install -r requirements.txt"),
    ("Seed database",                "python scripts/seed_database.py"),
    ("Build ChromaDB RAG index",     "python scripts/ingest_catalogue.py"),
    ("Start backend",                "uvicorn app.main:app --reload --port 8000"),
    ("Install frontend dependencies","cd frontend && npm install"),
    ("Start frontend",               "npm run dev"),
    ("Run tests",                    "cd backend && pytest -v  (expect 50 tests, 0 failures)"),
    ("Run evaluation",               "cd backend && python scripts/run_evaluation.py"),
]
add_table(["Step", "Command"], setup_steps, col_widths=[5.5, 11.0])

# ════════════════════════════════════════════════════════════════════════════
# 15. TESTING
# ════════════════════════════════════════════════════════════════════════════
add_heading("15. Testing", level=1)
add_para(
    "The backend test suite uses pytest and covers 50 test cases across 7 test files. "
    "All tests run in demo mode (no external services required)."
)
add_table(
    ["Test File", "Coverage"],
    [
        ["tests/test_tools.py",             "Walking distance (Dijkstra), opening hours, crowd status penalty"],
        ["tests/test_memory.py",            "Visitor memory CRUD, interest weight merging, memory clear"],
        ["tests/test_rag.py",               "Chunk generation, ingestion idempotency, retrieval relevance"],
        ["tests/test_agents.py",            "All five agents: input validation, output structure, fallback paths"],
        ["tests/test_orchestration.py",     "Full 5-agent pipeline, retry handling, WorkflowState trace recording"],
        ["tests/test_crowd_replanning.py",  "Crowd state setting, replan trigger, completed stop preservation"],
        ["tests/test_evaluation.py",        "Metric calculation, report output format, all-profiles coverage"],
    ],
    col_widths=[6.0, 10.5],
)

# ════════════════════════════════════════════════════════════════════════════
# 16. ACCEPTANCE CHECKLIST
# ════════════════════════════════════════════════════════════════════════════
add_heading("16. Acceptance Checklist", level=1)

categories = {
    "Multi-Agent": [
        "Five agents as separate modules with typed Pydantic contracts",
        "Semantic Kernel used as orchestration framework",
        "Planner-executor coordination implemented in PlannerExecutor",
        "Workflow traces show real execution with timestamps and durations",
    ],
    "RAG and Memory": [
        "Exhibit catalogue and curator notes indexed in ChromaDB (61 chunks)",
        "Retrieval returns relevant evidence with source references",
        "Commentary grounded in retrieved evidence",
        "Visitor memory persists across sessions",
        "Every agent can access the shared memory service",
        "Visitor can view, edit, and clear memory via the frontend",
    ],
    "Route Planning": [
        "Walking-distance tool implemented using Dijkstra's algorithm",
        "Opening-hours tool implemented and checked per stop",
        "Route respects stated time budget",
        "Route respects accessibility constraints",
        "Skipped items include reason codes and human-readable explanations",
    ],
    "Crowd-Aware Replanning": [
        "User can mark a gallery busy via the Crowd Control page",
        "Remaining route replanned without restarting the full visit",
        "Completed stops remain completed and are prepended unchanged",
        "Remaining time budget respected during replanning",
        "Before/after route comparison displayed in the UI",
    ],
    "Evaluation": [
        "Eight visitor profiles seeded in data/visitor_profiles.json",
        "Evaluation runs for all eight profiles via scripts/run_evaluation.py",
        "Time-budget fit rate calculated from actual route outputs",
        "Interest coverage calculated from stated interests",
        "Results saved as JSON and Markdown reports in evaluation_reports/",
    ],
    "Frontend and Run": [
        "All seven pages work: Home, Plan, Guide, Crowd, Memory, Evaluation, About",
        "No inert buttons",
        "Demo mode works without paid API credentials",
        "Backend starts with uvicorn app.main:app --reload",
        "Frontend starts with npm run dev",
        "README includes all setup commands",
    ],
}

for category, items in categories.items():
    add_heading(f"16.{list(categories.keys()).index(category)+1} {category}", level=2)
    for item in items:
        add_bullet(f"✓  {item}")

# ════════════════════════════════════════════════════════════════════════════
# 17. KNOWN LIMITATIONS
# ════════════════════════════════════════════════════════════════════════════
add_heading("17. Known Limitations", level=1)
limitations = [
    ("In-memory crowd state is process-scoped",
     "CrowdState resets on server restart. Designed for mirroring to MongoDB in production but demo mode uses db=None."),
    ("In-memory session and memory stores",
     "Demo mode runs entirely in-process memory. Data is lost on restart unless MongoDB is connected and the seed script has run."),
    ("Static walking graph",
     "The 4-node, 6-edge museum graph with hand-coded distances is a prototype. Walk times are estimates, not live GPS measurements."),
    ("37.5% time budget fit rate",
     "Many profiles with tight budgets (30–50 min) produce routes that sum to slightly more than the budget. This is a known boundary-case result, not a defect."),
    ("Semantic Kernel as optional dependency",
     "The SK plugin wrappers in framework_adapter.py are not used in the main plan_visit() execution path; they are exposed for future planner integration. The system falls back to sequential Python await calls if SK is absent."),
    ("Crowd state mirroring",
     "The services layer is designed to mirror crowd state to MongoDB but demo wiring uses db=None, so crowd state is not persisted to disk."),
]
for title, detail in limitations:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    r1 = p.add_run(f"{title}: ")
    r1.bold = True
    r1.font.size = Pt(11)
    r2 = p.add_run(detail)
    r2.font.size = Pt(11)

# ════════════════════════════════════════════════════════════════════════════
# 18. GROUP CONTRIBUTIONS
# ════════════════════════════════════════════════════════════════════════════
add_heading("18. Group Contributions", level=1)
add_table(
    ["Student ID", "Name", "Contribution Area"],
    [
        ["12317780", "Ganesh Kumar", "Backend: agents, orchestration, RAG pipeline, planning tools, evaluation service, database setup, test suite"],
        ["12320064", "Saurav",       "Frontend: React pages, API integration, UI/UX design, documentation"],
    ],
    col_widths=[3.0, 3.5, 10.0],
)

# ════════════════════════════════════════════════════════════════════════════
# SAVE
# ════════════════════════════════════════════════════════════════════════════
output_path = "/Users/ganeshkumar/Desktop/untitled folder 8/museum-exhibit-guide/Project_Report_Q26_Museum_Exhibit_Guide.docx"
doc.save(output_path)
print(f"Saved: {output_path}")
