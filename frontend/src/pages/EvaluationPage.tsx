import { useState, useEffect } from 'react'
import { runEvaluation, getLatestReport } from '../api/client'
import type { EvaluationReport } from '../types'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'

export default function EvaluationPage() {
  const [report, setReport] = useState<EvaluationReport | null>(null)
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    getLatestReport()
      .then(r => { if (r.data?.profiles) setReport(r.data) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleRun = async () => {
    setRunning(true); setError('')
    try {
      const res = await runEvaluation()
      setReport(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message)
    } finally { setRunning(false) }
  }

  if (loading) return <LoadingSpinner />
  if (running) return <LoadingSpinner message="Running evaluation for all 8 visitor profiles… (may take 30–60 seconds)" />

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-display font-bold">Evaluation Dashboard</h1>
          <p className="text-museum-muted text-sm">Automated metrics across all 8 visitor profiles.</p>
        </div>
        <button onClick={handleRun} className="btn-primary">▶ Run Evaluation</button>
      </div>

      {error && <ErrorMessage message={error} />}

      {!report && !error && (
        <div className="card text-museum-muted text-sm">No report yet. Click "Run Evaluation" to generate one.</div>
      )}

      {report && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
            {[
              { label: 'Time Budget Fit Rate', value: `${report.time_budget_fit_rate_pct.toFixed(1)}%`, color: report.time_budget_fit_rate_pct >= 50 ? 'text-green-600' : 'text-amber-600' },
              { label: 'Avg Interest Coverage', value: `${report.average_interest_coverage_pct.toFixed(1)}%`, color: 'text-blue-600' },
              { label: 'Avg Exhibits / Route', value: report.average_exhibits_per_route.toFixed(1), color: 'text-museum-text' },
              { label: 'Avg Walking Time', value: `${report.average_walking_minutes.toFixed(1)} min`, color: 'text-museum-text' },
              { label: 'Accessibility Rate', value: `${report.accessibility_compliance_rate_pct.toFixed(1)}%`, color: 'text-green-600' },
              { label: 'Opening Hours Rate', value: `${report.opening_hours_compliance_rate_pct.toFixed(1)}%`, color: 'text-green-600' },
            ].map((m, i) => (
              <div key={i} className="card text-center">
                <div className={`text-3xl font-bold ${m.color}`}>{m.value}</div>
                <div className="text-xs text-museum-muted mt-1">{m.label}</div>
              </div>
            ))}
          </div>

          <p className="text-xs text-museum-muted mb-3">Report generated: {new Date(report.run_at).toLocaleString()}</p>

          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-museum-light border-b border-museum-border">
                  <th className="text-left p-2 font-semibold">Visitor</th>
                  <th className="p-2">Budget</th>
                  <th className="p-2">Route</th>
                  <th className="p-2">Fit</th>
                  <th className="p-2">Coverage %</th>
                  <th className="p-2">Exhibits</th>
                  <th className="p-2">Accessibility</th>
                </tr>
              </thead>
              <tbody>
                {report.profiles.map(p => (
                  <tr key={p.visitor_id} className="border-b border-museum-border hover:bg-museum-light">
                    <td className="p-2">
                      <div className="font-medium text-xs">{p.visitor_id}</div>
                      <div className="text-museum-muted text-xs truncate max-w-32">{p.display_name}</div>
                    </td>
                    <td className="p-2 text-center">{p.time_budget_minutes}m</td>
                    <td className="p-2 text-center">{p.total_route_minutes.toFixed(0)}m</td>
                    <td className="p-2 text-center">{p.time_budget_fit ? <span className="badge badge-green">✓</span> : <span className="badge badge-amber">✗</span>}</td>
                    <td className="p-2 text-center">
                      <span className={p.interest_coverage_pct >= 80 ? 'text-green-600 font-semibold' : 'text-amber-600 font-semibold'}>
                        {p.interest_coverage_pct.toFixed(0)}%
                      </span>
                    </td>
                    <td className="p-2 text-center">{p.num_exhibits_in_route}</td>
                    <td className="p-2 text-center">{p.accessibility_compliant ? <span className="badge badge-green">✓</span> : <span className="badge badge-red">✗</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
