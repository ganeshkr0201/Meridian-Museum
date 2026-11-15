import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-16">
      <div className="text-center mb-12">
        <div className="text-5xl mb-4">🏛</div>
        <h1 className="text-4xl font-display font-bold text-museum-text mb-3">
          Meridian Museum
        </h1>
        <p className="text-xl text-museum-muted mb-2">Personalised Exhibit Guide</p>
        <span className="badge badge-amber">Demo Dataset — Fictional Collection</span>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-12">
        <div className="card flex flex-col gap-3">
          <h2 className="text-xl font-display font-semibold">Plan Your Visit</h2>
          <p className="text-museum-muted text-sm flex-1">
            Tell us your interests, available time, and accessibility needs. Our
            multi-agent system will generate a personalised route with grounded
            commentary for every stop.
          </p>
          <Link to="/plan" className="btn-primary text-center mt-auto">
            Plan My Visit →
          </Link>
        </div>
        <div className="card flex flex-col gap-3">
          <h2 className="text-xl font-display font-semibold">Explore Demo Museum</h2>
          <p className="text-museum-muted text-sm flex-1">
            Jump straight in with a pre-filled visitor profile to see the full
            agent workflow, route generation, and crowd-aware replanning without
            any configuration.
          </p>
          <Link
            to="/plan?demo=true"
            className="btn-secondary text-center mt-auto"
          >
            Run Demo Mode →
          </Link>
        </div>
      </div>

      <div className="card mb-8">
        <h2 className="text-xl font-display font-semibold mb-4">How It Works</h2>
        <div className="grid sm:grid-cols-5 gap-4 text-sm text-center">
          {[
            { icon: '👤', label: 'Visitor Profile Agent', desc: 'Validates preferences & reads/writes memory' },
            { icon: '🔍', label: 'Exhibit Retrieval Agent', desc: 'RAG over catalogue & curator notes' },
            { icon: '🗺️', label: 'Route Planner Agent', desc: 'Heuristic planning with walking & hours tools' },
            { icon: '✍️', label: 'Commentary Writer', desc: 'Grounded notes with citations' },
            { icon: '✅', label: 'Guide Manager', desc: 'Validation & final assembly' },
          ].map((a, i) => (
            <div key={i} className="bg-museum-light rounded-lg p-3 flex flex-col items-center gap-1">
              <div className="text-2xl">{a.icon}</div>
              <div className="font-semibold text-museum-accent text-xs">{a.label}</div>
              <div className="text-museum-muted text-xs">{a.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid sm:grid-cols-3 gap-4 text-sm text-center">
        {[
          { label: '12 Exhibits', icon: '🖼️' },
          { label: '4 Galleries', icon: '🏛️' },
          { label: '8 Visitor Profiles', icon: '👥' },
        ].map((s, i) => (
          <div key={i} className="card flex items-center justify-center gap-2 py-4">
            <span className="text-2xl">{s.icon}</span>
            <span className="font-semibold">{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
