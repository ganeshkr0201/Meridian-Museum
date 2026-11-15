import { useState } from 'react'
import { getVisitor, updateVisitorPrefs, clearVisitorMemory } from '../api/client'
import type { VisitorMemory } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'

export default function MemoryPage() {
  const [visitorId, setVisitorId] = useState('')
  const [memory, setMemory] = useState<VisitorMemory | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  const load = async () => {
    if (!visitorId.trim()) { setError('Enter a visitor ID.'); return }
    setLoading(true); setError('')
    try {
      const res = await getVisitor(visitorId)
      setMemory(res.data)
    } catch (e: any) { setError(e?.response?.status === 404 ? 'Visitor not found.' : e.message) }
    finally { setLoading(false) }
  }

  const handleClear = async () => {
    if (!memory) return
    if (!confirm('Clear all saved memory for this visitor?')) return
    await clearVisitorMemory(memory.visitor_id)
    setMemory(null); setMsg('Memory cleared.')
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-display font-bold mb-2">Visitor Memory</h1>
      <p className="text-museum-muted text-sm mb-6">View and manage your saved preferences and visit history.</p>
      {error && <ErrorMessage message={error} />}
      {msg && <div className="bg-green-50 border border-green-200 rounded p-3 text-green-700 text-sm mb-4">{msg}</div>}

      <div className="flex gap-2 mb-6">
        <input
          className="flex-1 border border-museum-border rounded px-3 py-2 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-museum-accent"
          value={visitorId}
          onChange={e => setVisitorId(e.target.value)}
          placeholder="Enter visitor ID (e.g. visitor_01)"
        />
        <button onClick={load} className="btn-primary text-sm">Load</button>
      </div>

      {loading && <LoadingSpinner />}

      {memory && (
        <div className="card">
          <h2 className="font-display font-semibold text-lg mb-3">{memory.display_name}</h2>
          <div className="grid grid-cols-2 gap-3 text-sm mb-4">
            <div><span className="font-medium">Visitor ID:</span> <span className="text-museum-muted">{memory.visitor_id}</span></div>
            <div><span className="font-medium">Language:</span> <span className="text-museum-muted">{memory.preferred_language}</span></div>
            <div><span className="font-medium">Commentary:</span> <span className="text-museum-muted">{memory.preferred_commentary_length}</span></div>
            <div><span className="font-medium">Updated:</span> <span className="text-museum-muted">{new Date(memory.updated_at).toLocaleDateString()}</span></div>
          </div>
          <div className="mb-3">
            <span className="font-medium text-sm">Interests:</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {memory.interests.map(i => <span key={i} className="badge badge-blue">{i.replace(/_/g,' ')}</span>)}
            </div>
          </div>
          {memory.accessibility_needs?.length > 0 && (
            <div className="mb-3">
              <span className="font-medium text-sm">Accessibility:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {memory.accessibility_needs.map(a => <span key={a} className="badge badge-amber">{a.replace(/_/g,' ')}</span>)}
              </div>
            </div>
          )}
          {memory.previously_visited_exhibits?.length > 0 && (
            <div className="mb-3">
              <span className="font-medium text-sm">Previously visited:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {memory.previously_visited_exhibits.map(e => <span key={e} className="badge badge-green">{e}</span>)}
              </div>
            </div>
          )}
          <button onClick={handleClear} className="btn-secondary text-sm text-red-600 border-red-200 hover:bg-red-50 mt-2">
            🗑 Clear Memory
          </button>
        </div>
      )}
    </div>
  )
}
