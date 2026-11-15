import { useState, useEffect } from 'react'
import { useParams, useLocation, Link } from 'react-router-dom'
import { getVisit, completeStop, submitFeedback } from '../api/client'
import type { VisitGuide as Guide, RouteStop } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'

function StatusBadge({ fit }: { fit: boolean }) {
  return fit
    ? <span className="badge badge-green">✓ Within budget</span>
    : <span className="badge badge-amber">⚠ Slightly over budget</span>
}

function StopCard({ stop, commentary, onComplete }: {
  stop: RouteStop
  commentary?: { commentary: string; interest_match_reason: string; source_references: string[]; did_you_know: string }
  onComplete: () => void
}) {
  const [feedbackSent, setFeedbackSent] = useState(false)
  return (
    <div className={`card border-l-4 ${stop.is_completed ? 'border-l-green-400 opacity-70' : 'border-l-museum-accent'}`}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <div>
          <span className="text-xs text-museum-muted">Stop {stop.sequence}</span>
          <h3 className="font-display font-semibold text-lg leading-tight">{stop.exhibit_title}</h3>
          <span className="text-sm text-museum-muted">{stop.gallery_name}</span>
        </div>
        <div className="text-right shrink-0">
          <div className="text-sm font-semibold">{stop.visit_duration_minutes} min</div>
          {stop.walking_time_from_previous_minutes > 0 && (
            <div className="text-xs text-museum-muted">+{stop.walking_time_from_previous_minutes.toFixed(1)} min walk</div>
          )}
        </div>
      </div>

      <div className="flex gap-2 mb-3 flex-wrap">
        <span className={`badge ${stop.accessibility_status === 'accessible' ? 'badge-green' : 'badge-red'}`}>
          {stop.accessibility_status}
        </span>
        <span className="badge badge-blue">{stop.opening_status}</span>
        {stop.walking_distance_from_previous_m > 0 && (
          <span className="badge badge-blue">{stop.walking_distance_from_previous_m}m walk</span>
        )}
      </div>

      {commentary && (
        <div className="text-sm text-museum-text mb-2">
          <p className="mb-2">{commentary.commentary}</p>
          <p className="text-museum-accent italic text-xs mb-1">{commentary.interest_match_reason}</p>
          {commentary.did_you_know && (
            <p className="bg-museum-light rounded px-3 py-2 text-xs mb-1">💡 {commentary.did_you_know}</p>
          )}
          <div className="text-xs text-museum-muted">
            Sources: {commentary.source_references.join(', ')}
          </div>
        </div>
      )}

      {!stop.is_completed && (
        <div className="flex gap-2 mt-3">
          <button onClick={onComplete} className="btn-primary text-sm py-1 px-3">Mark Visited ✓</button>
          {!feedbackSent && (
            <>
              <button onClick={() => setFeedbackSent(true)} className="btn-secondary text-sm py-1 px-3">👍</button>
              <button onClick={() => setFeedbackSent(true)} className="btn-secondary text-sm py-1 px-3">👎</button>
            </>
          )}
        </div>
      )}
      {stop.is_completed && <div className="text-green-600 text-sm font-semibold mt-2">✓ Visited</div>}
    </div>
  )
}

export default function VisitGuide() {
  const { visitId } = useParams()
  const location = useLocation()
  const [guide, setGuide] = useState<Guide | null>(location.state?.guide || null)
  const [loading, setLoading] = useState(!guide)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'route' | 'trace' | 'skipped' | 'sources'>('route')

  useEffect(() => {
    if (!guide && visitId) {
      getVisit(visitId).then(r => setGuide(r.data)).catch(e => setError(e.message)).finally(() => setLoading(false))
    }
  }, [visitId])

  const handleComplete = async (exhibitId: string) => {
    if (!visitId) return
    const res = await completeStop(visitId, exhibitId)
    setGuide(res.data)
  }

  if (loading) return <LoadingSpinner message="Loading your visit guide…" />
  if (error) return <div className="max-w-3xl mx-auto px-4 py-10"><ErrorMessage message={error} /></div>
  if (!guide) return <div className="max-w-3xl mx-auto px-4 py-10 text-museum-muted">No guide found.</div>

  const tabs = ['route', 'trace', 'skipped', 'sources'] as const

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="card mb-6">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-display font-bold">Your Visit Guide</h1>
            <p className="text-xs text-museum-muted mt-1">Visit ID: {guide.visit_id}</p>
            {guide.crowd_replan_version > 0 && (
              <p className="text-xs text-amber-600 mt-1">🔄 Replanned (version {guide.crowd_replan_version}): {guide.replan_explanation}</p>
            )}
          </div>
          <StatusBadge fit={guide.time_budget_fit} />
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4 text-center text-sm">
          <div><div className="font-bold text-lg">{guide.total_visit_minutes.toFixed(0)}</div><div className="text-museum-muted text-xs">Visit min</div></div>
          <div><div className="font-bold text-lg">{guide.total_walking_minutes.toFixed(0)}</div><div className="text-museum-muted text-xs">Walk min</div></div>
          <div><div className="font-bold text-lg">{guide.route.length}</div><div className="text-museum-muted text-xs">Stops</div></div>
        </div>
        <div className="mt-3 text-xs text-museum-muted">
          Interest coverage: {Object.entries(guide.interest_coverage).map(([k, v]) => (
            <span key={k} className={`badge mr-1 ${v ? 'badge-green' : 'badge-red'}`}>{k.replace(/_/g,' ')}</span>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b border-museum-border">
        {tabs.map(t => (
          <button key={t} onClick={() => setActiveTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${activeTab === t ? 'border-museum-accent text-museum-accent' : 'border-transparent text-museum-muted hover:text-museum-text'}`}>
            {t}
          </button>
        ))}
      </div>

      {activeTab === 'route' && (
        <div className="flex flex-col gap-4">
          {guide.route.length === 0 && <p className="text-museum-muted text-sm">No stops in route.</p>}
          {guide.route.map(stop => (
            <StopCard
              key={stop.exhibit_id}
              stop={stop}
              commentary={guide.commentaries[stop.exhibit_id]}
              onComplete={() => handleComplete(stop.exhibit_id)}
            />
          ))}
          <div className="mt-2 text-center">
            <Link to={`/crowd?visitId=${guide.visit_id}`} className="btn-secondary text-sm">
              🔄 Mark Gallery Busy & Replan
            </Link>
          </div>
        </div>
      )}

      {activeTab === 'trace' && (
        <div className="flex flex-col gap-3">
          {guide.workflow_trace.map((entry, i) => (
            <div key={i} className={`card border-l-4 ${entry.status === 'completed' ? 'border-l-green-400' : entry.status === 'failed' ? 'border-l-red-400' : 'border-l-gray-300'}`}>
              <div className="flex items-center justify-between">
                <span className="font-semibold text-sm">{entry.agent_name}</span>
                <span className={`badge ${entry.status === 'completed' ? 'badge-green' : entry.status === 'failed' ? 'badge-red' : 'badge-blue'}`}>{entry.status}</span>
              </div>
              {entry.duration_ms && <div className="text-xs text-museum-muted mt-1">{entry.duration_ms.toFixed(0)} ms</div>}
              {entry.input_summary && <div className="text-xs mt-1"><span className="font-medium">In:</span> {entry.input_summary}</div>}
              {entry.output_summary && <div className="text-xs mt-0.5"><span className="font-medium">Out:</span> {entry.output_summary}</div>}
              {entry.error_message && <div className="text-xs text-red-600 mt-1">{entry.error_message}</div>}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'skipped' && (
        <div className="flex flex-col gap-3">
          {guide.skipped_items.length === 0 && <p className="text-museum-muted text-sm">No exhibits were skipped.</p>}
          {guide.skipped_items.map((s, i) => (
            <div key={i} className="card border-l-4 border-l-gray-300">
              <div className="font-semibold text-sm">{s.title}</div>
              <div className="text-xs text-museum-muted mt-1"><span className="badge badge-amber mr-1">{s.reason_code}</span>{s.human_readable_reason}</div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'sources' && (
        <div className="flex flex-col gap-3">
          {guide.sources.slice(0, 10).map((s, i) => (
            <div key={i} className="card">
              <div className="font-semibold text-sm">{s.source_title}</div>
              <div className="text-xs text-museum-muted mt-1">Exhibit: {s.exhibit_id} | Score: {s.relevance_score.toFixed(3)}</div>
              <div className="text-xs mt-1 text-museum-text line-clamp-2">{s.chunk_text}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
