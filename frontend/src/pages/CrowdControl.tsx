import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getCrowdStatus, updateCrowd, replanVisit, getVisit } from '../api/client'
import type { CrowdStatus, VisitGuide } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'

const STATES = ['normal', 'moderate', 'busy', 'closed'] as const
const STATE_COLORS: Record<string, string> = {
  normal: 'badge-green', moderate: 'badge-amber', busy: 'badge-red', closed: 'badge-red',
}

export default function CrowdControl() {
  const [params] = useSearchParams()
  const visitId = params.get('visitId') || ''
  const [crowd, setCrowd] = useState<Record<string, CrowdStatus>>({})
  const [guide, setGuide] = useState<VisitGuide | null>(null)
  const [newGuide, setNewGuide] = useState<VisitGuide | null>(null)
  const [loading, setLoading] = useState(true)
  const [replanning, setReplanning] = useState(false)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const crowdRes = await getCrowdStatus()
        setCrowd(crowdRes.data)
        if (visitId) {
          const guideRes = await getVisit(visitId)
          setGuide(guideRes.data)
        }
      } catch (e: any) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [visitId])

  const handleUpdate = async (galleryId: string, state: string) => {
    try {
      await updateCrowd(galleryId, state)
      const res = await getCrowdStatus()
      setCrowd(res.data)
      setMsg(`Gallery ${galleryId} set to ${state}.`)
    } catch (e: any) { setError(e.message) }
  }

  const handleReplan = async (galleryId: string) => {
    if (!visitId) { setError('No active visit. Plan a visit first.'); return }
    setReplanning(true)
    try {
      const res = await replanVisit(visitId, galleryId)
      setNewGuide(res.data)
      setMsg(`Route replanned avoiding gallery ${galleryId}.`)
    } catch (e: any) { setError(e.message) }
    finally { setReplanning(false) }
  }

  if (loading) return <LoadingSpinner />
  if (replanning) return <LoadingSpinner message="Replanning route…" />

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-display font-bold mb-2">Crowd Control</h1>
      <p className="text-museum-muted text-sm mb-6">
        Update gallery crowd status and trigger crowd-aware replanning for the remaining route.
      </p>
      {error && <ErrorMessage message={error} />}
      {msg && <div className="bg-green-50 border border-green-200 rounded p-3 text-green-700 text-sm mb-4">{msg}</div>}

      {!visitId && (
        <div className="bg-museum-light border border-museum-border rounded p-3 text-sm mb-6 text-museum-muted">
          No active visit loaded. <a href="/plan" className="text-museum-accent underline">Plan a visit</a> first to enable replanning.
        </div>
      )}

      <div className="flex flex-col gap-4 mb-8">
        {Object.entries(crowd).map(([gid, status]) => (
          <div key={gid} className="card">
            <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
              <div>
                <span className="font-semibold">{gid}</span>
                <span className={`badge ml-2 ${STATE_COLORS[status.crowd_state] || 'badge-blue'}`}>{status.crowd_state}</span>
              </div>
              <p className="text-xs text-museum-muted">{status.description}</p>
            </div>
            <div className="flex gap-2 flex-wrap">
              {STATES.map(s => (
                <button key={s} onClick={() => handleUpdate(gid, s)}
                  className={`px-3 py-1 text-xs rounded border transition-colors ${status.crowd_state === s ? 'bg-museum-accent text-white border-museum-accent' : 'border-museum-border hover:bg-museum-light'}`}>
                  {s}
                </button>
              ))}
              {visitId && (
                <button onClick={() => handleReplan(gid)}
                  className="ml-auto btn-primary text-xs py-1 px-3">
                  🔄 Replan Avoiding This Gallery
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {newGuide && (
        <div className="card border-t-4 border-t-museum-accent">
          <h2 className="font-display font-bold text-lg mb-2">Updated Route</h2>
          <p className="text-xs text-museum-muted mb-3">{newGuide.replan_explanation}</p>
          <div className="flex flex-col gap-2">
            {newGuide.route.filter(s => !s.is_completed).map(stop => (
              <div key={stop.exhibit_id} className="flex items-center justify-between text-sm border-b border-museum-border pb-2">
                <span>{stop.sequence}. {stop.exhibit_title}</span>
                <span className="text-museum-muted text-xs">{stop.gallery_name} · {stop.visit_duration_minutes} min</span>
              </div>
            ))}
          </div>
          <a href={`/guide/${newGuide.visit_id}`} className="btn-primary text-sm mt-4 inline-block">View Full Guide →</a>
        </div>
      )}
    </div>
  )
}
