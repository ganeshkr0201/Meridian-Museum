export default function About() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-display font-bold mb-2">About & Architecture</h1>
      <p className="text-museum-muted text-sm mb-8">How the multi-agent system works.</p>

      <div className="flex flex-col gap-6">
        {[
          {
            icon: '👤', title: 'Visitor Profile Agent',
            desc: 'Validates and normalises visitor form input. Reads existing memory for returning visitors and writes updated preferences to the shared MongoDB memory store. Produces a typed VisitorProfile passed to all downstream agents.',
          },
          {
            icon: '🔍', title: 'Exhibit Retrieval Agent (RAG)',
            desc: 'Embeds visitor interests using all-MiniLM-L6-v2 and queries ChromaDB for the most relevant chunks from the exhibit catalogue and 13 curator notes. Returns RetrievedEvidence objects with source IDs and relevance scores.',
          },
          {
            icon: '🗺️', title: 'Route Planner Agent',
            desc: 'Uses a heuristic scoring function combining interest relevance, crowd penalty, and walking time. Calls the Walking Distance Tool (Dijkstra on a seeded museum graph) and the Opening Hours Tool to verify every stop is feasible before including it.',
          },
          {
            icon: '✍️', title: 'Commentary Writer Agent',
            desc: 'Writes 2–6 sentence commentary per exhibit grounded exclusively in retrieved evidence chunks. In demo mode (LLM_MODE=demo) this is deterministic. With LLM_MODE=openai it calls an OpenAI-compatible endpoint. Every commentary includes source references.',
          },
          {
            icon: '✅', title: 'Guide Manager Agent',
            desc: 'Compiles and validates the final guide. Recalculates route totals server-side, checks opening-hours feasibility for every stop, verifies commentary coverage, and computes interest coverage from exhibit tags.',
          },
        ].map((a, i) => (
          <div key={i} className="card">
            <h2 className="font-display font-semibold text-lg mb-2">{a.icon} {a.title}</h2>
            <p className="text-sm text-museum-text">{a.desc}</p>
          </div>
        ))}

        <div className="card">
          <h2 className="font-display font-semibold text-lg mb-2">🎯 Planner-Executor Coordination</h2>
          <p className="text-sm text-museum-text mb-2">
            The <code className="bg-museum-light px-1 rounded">PlannerExecutor</code> orchestrator (using Semantic Kernel — Microsoft's open-source agent framework) coordinates all five agents in dependency order. It owns the shared WorkflowState, records execution traces for every agent, and supports up to 2 retries per agent on transient failures.
          </p>
          <p className="text-sm text-museum-text">
            Each agent receives only typed input contracts from the orchestrator — no hidden global state. This differs from a single chatbot because each agent has a dedicated responsibility, observable execution, and the orchestrator can selectively re-run failed stages.
          </p>
        </div>

        <div className="card">
          <h2 className="font-display font-semibold text-lg mb-2">🧠 Shared Visitor Memory</h2>
          <p className="text-sm text-museum-text">
            All agents access a shared <code className="bg-museum-light px-1 rounded">VisitorMemoryService</code> backed by MongoDB (or in-memory in demo mode). The Visitor Profile Agent writes on every session; other agents read. Memory stores interests, accessibility needs, visited exhibits, explicit feedback, and visit history. Persistent mode carries preferences across separate sessions.
          </p>
        </div>

        <div className="card">
          <h2 className="font-display font-semibold text-lg mb-2">🔄 Crowd-Aware Replanning</h2>
          <p className="text-sm text-museum-text">
            When a visitor marks a gallery busy, the system re-runs the Route Planner Agent with the busy gallery excluded from the candidate set. Completed stops are preserved, elapsed time is subtracted from the budget, and opening-hours checks are re-run. The replan version and explanation appear in the guide.
          </p>
        </div>

        <div className="card">
          <h2 className="font-display font-semibold text-lg mb-2">📊 Architecture Diagram</h2>
          <pre className="bg-museum-light rounded p-4 text-xs overflow-x-auto text-museum-text">
{`Visitor Form
     │
     ▼
PlannerExecutor (Semantic Kernel)
     │
     ├─► VisitorProfileAgent  ◄──► MongoDB (VisitorMemory)
     │
     ├─► ExhibitRetrievalAgent ◄─► ChromaDB (61 chunks)
     │        └─ sentence-transformers embeddings
     │
     ├─► RoutePlannerAgent
     │        ├─ WalkingDistanceTool  (Dijkstra graph)
     │        ├─ OpeningHoursTool     (seeded data)
     │        └─ CrowdStatusTool      (in-memory + DB)
     │
     ├─► CommentaryWriterAgent  (demo mode / OpenAI)
     │
     └─► GuideManagerAgent  ──► VisitGuide (validated)
                                     │
                                     ▼
                              FastAPI REST API
                                     │
                                     ▼
                              React Frontend`}
          </pre>
        </div>
      </div>
    </div>
  )
}
