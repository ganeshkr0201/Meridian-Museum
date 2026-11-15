import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { planVisit } from '../api/client'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'

const INTERESTS = [
  'ancient_history','archaeology','science','technology',
  'art','textiles','coins','local_culture','natural_history','regional_craft',
]
const ACCESSIBILITY = ['none','wheelchair','step_free','reduced_walking','avoid_stairs','seating_breaks']
const DEMO = {
  display_name: 'Demo Visitor',
  interests: ['ancient_history','science','art'],
  time_budget_minutes: 60,
  accessibility_needs: [],
  language: 'en',
  commentary_length: 'medium',
  memory_mode: 'guest',
}

export default function PlanVisit() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    display_name: '',
    interests: [] as string[],
    time_budget_minutes: 60,
    accessibility_needs: [] as string[],
    language: 'en',
    commentary_length: 'medium',
    memory_mode: 'persistent',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (params.get('demo') === 'true') {
      setForm(DEMO as typeof form)
    }
  }, [params])

  const toggleInterest = (i: string) => {
    setForm(f => ({
      ...f,
      interests: f.interests.includes(i) ? f.interests.filter(x => x !== i) : [...f.interests, i],
    }))
  }

  const toggleAccessibility = (a: string) => {
    if (a === 'none') { setForm(f => ({ ...f, accessibility_needs: [] })); return }
    setForm(f => ({
      ...f,
      accessibility_needs: f.accessibility_needs.includes(a)
        ? f.accessibility_needs.filter(x => x !== a)
        : [...f.accessibility_needs, a],
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.display_name.trim()) { setError('Please enter your name.'); return }
    if (form.interests.length === 0) { setError('Please select at least one interest.'); return }
    setError('')
    setLoading(true)
    try {
      const res = await planVisit(form)
      navigate(`/guide/${res.data.visit_id}`, { state: { guide: res.data } })
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Planning failed.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <LoadingSpinner message="Agents are planning your personalised route… (this may take 10–20 seconds)" />

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-display font-bold mb-2">Plan Your Visit</h1>
      <p className="text-museum-muted mb-6 text-sm">Fill in your preferences and we'll build a personalised route.</p>

      {error && <ErrorMessage message={error} />}

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {/* Name */}
        <div>
          <label className="block text-sm font-semibold mb-1">Your Name</label>
          <input
            className="w-full border border-museum-border rounded px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-museum-accent"
            value={form.display_name}
            onChange={e => setForm(f => ({ ...f, display_name: e.target.value }))}
            placeholder="e.g. Aryan"
            maxLength={100}
          />
        </div>

        {/* Interests */}
        <div>
          <label className="block text-sm font-semibold mb-2">Interests</label>
          <div className="flex flex-wrap gap-2">
            {INTERESTS.map(i => (
              <button
                type="button"
                key={i}
                onClick={() => toggleInterest(i)}
                className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                  form.interests.includes(i)
                    ? 'bg-museum-accent text-white border-museum-accent'
                    : 'border-museum-border hover:bg-museum-light'
                }`}
              >
                {i.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Time Budget */}
        <div>
          <label className="block text-sm font-semibold mb-1">
            Time Budget: <span className="text-museum-accent">{form.time_budget_minutes} minutes</span>
          </label>
          <input
            type="range" min={15} max={180} step={5}
            value={form.time_budget_minutes}
            onChange={e => setForm(f => ({ ...f, time_budget_minutes: +e.target.value }))}
            className="w-full accent-amber-700"
          />
          <div className="flex justify-between text-xs text-museum-muted mt-1">
            <span>15 min</span><span>180 min</span>
          </div>
        </div>

        {/* Accessibility */}
        <div>
          <label className="block text-sm font-semibold mb-2">Accessibility Needs</label>
          <div className="flex flex-wrap gap-2">
            {ACCESSIBILITY.map(a => (
              <button
                type="button"
                key={a}
                onClick={() => toggleAccessibility(a)}
                className={`px-3 py-1 rounded-full text-sm border transition-colors ${
                  (a === 'none' && form.accessibility_needs.length === 0) || form.accessibility_needs.includes(a)
                    ? 'bg-museum-accent text-white border-museum-accent'
                    : 'border-museum-border hover:bg-museum-light'
                }`}
              >
                {a.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Options row */}
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-semibold mb-1">Language</label>
            <select
              className="w-full border border-museum-border rounded px-2 py-1.5 bg-white text-sm"
              value={form.language}
              onChange={e => setForm(f => ({ ...f, language: e.target.value }))}
            >
              <option value="en">English</option>
              <option value="hi">Hindi</option>
              <option value="fr">French</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Commentary</label>
            <select
              className="w-full border border-museum-border rounded px-2 py-1.5 bg-white text-sm"
              value={form.commentary_length}
              onChange={e => setForm(f => ({ ...f, commentary_length: e.target.value }))}
            >
              <option value="short">Short</option>
              <option value="medium">Medium</option>
              <option value="long">Long</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Memory</label>
            <select
              className="w-full border border-museum-border rounded px-2 py-1.5 bg-white text-sm"
              value={form.memory_mode}
              onChange={e => setForm(f => ({ ...f, memory_mode: e.target.value }))}
            >
              <option value="persistent">Persistent</option>
              <option value="guest">Guest</option>
            </select>
          </div>
        </div>

        <button type="submit" className="btn-primary py-3 text-base">
          Generate My Visit Guide →
        </button>
      </form>
    </div>
  )
}
