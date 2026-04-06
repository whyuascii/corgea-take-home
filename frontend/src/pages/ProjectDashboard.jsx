import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'
import StatusBadge from '../components/StatusBadge'
import TrendsChart from '../components/TrendsChart'
import QuickUpload from '../components/QuickUpload'
import useWebSocket from '../hooks/useWebSocket'

const STAT_COLOR_MAP = {
  gray: {
    border: 'border-l-gray-500',
    dot: 'bg-gray-500',
    text: 'text-gray-400',
    value: 'text-gray-100',
  },
  indigo: {
    border: 'border-l-indigo-500',
    dot: 'bg-indigo-500',
    text: 'text-indigo-400',
    value: 'text-indigo-100',
  },
  green: {
    border: 'border-l-green-500',
    dot: 'bg-green-500',
    text: 'text-green-400',
    value: 'text-green-100',
  },
  red: {
    border: 'border-l-red-500',
    dot: 'bg-red-500',
    text: 'text-red-400',
    value: 'text-red-100',
  },
  yellow: {
    border: 'border-l-yellow-500',
    dot: 'bg-yellow-500',
    text: 'text-yellow-400',
    value: 'text-yellow-100',
  },
  purple: {
    border: 'border-l-purple-500',
    dot: 'bg-purple-500',
    text: 'text-purple-400',
    value: 'text-purple-100',
  },
}

function StatCard({ label, value, color }) {
  const colors = STAT_COLOR_MAP[color] || STAT_COLOR_MAP.gray
  return (
    <div
      className={`bg-gray-900 border border-gray-800 rounded-xl p-5 border-l-4 ${colors.border}`}
    >
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-3 h-3 rounded-full ${colors.dot}`} />
        <span className={`text-xs uppercase tracking-wide ${colors.text}`}>
          {label}
        </span>
      </div>
      <p className={`text-3xl font-bold ${colors.value}`}>{value}</p>
    </div>
  )
}

export default function ProjectDashboard() {
  const { slug } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const fetchDashboard = async () => {
    try {
      const r = await api.get(`/projects/${slug}/findings/summary/`)
      setData(r.data)
    } catch {
      setError('Failed to load dashboard data')
    }
  }

  const handleWsMessage = useCallback((msg) => {
    if (msg.event === 'scan_complete') {
      fetchDashboard()
    }
  }, [slug])

  useWebSocket(`/ws/projects/${slug}/scans/`, {
    enabled: !!slug,
    onMessage: handleWsMessage,
  })

  useEffect(() => {
    fetchDashboard()
  }, [slug])

  if (error) return <p className="text-red-400">{error}</p>
  if (!data) return <p className="text-gray-500">Loading...</p>

  const { status_counts, total_active, severity_counts, total_findings, top_rules, recent_scans } = data

  const statsCards = [
    { label: 'Total Findings', value: total_findings, color: 'gray' },
    { label: 'Active', value: total_active, color: 'indigo' },
    { label: 'Resolved', value: status_counts?.resolved || 0, color: 'green' },
    { label: 'Critical', value: severity_counts?.error || 0, color: 'red' },
    { label: 'Warnings', value: severity_counts?.warning || 0, color: 'yellow' },
    { label: 'False Positives', value: status_counts?.false_positive || 0, color: 'purple' },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      {/* Stats Grid - 2 rows x 3 columns */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {statsCards.map((card) => (
          <StatCard
            key={card.label}
            label={card.label}
            value={card.value}
            color={card.color}
          />
        ))}
      </div>

      {/* Quick Upload */}
      <QuickUpload slug={slug} onUploadComplete={fetchDashboard} />

      {/* Trends Chart */}
      <TrendsChart slug={slug} />

      {/* Top Offending Rules */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
        <h2 className="font-semibold mb-3">Top Offending Rules</h2>
        {top_rules.length === 0 ? (
          <p className="text-gray-500 text-sm">No active findings</p>
        ) : (
          <div className="space-y-1">
            {top_rules.map((r) => (
              <Link
                key={r.id}
                to={`/projects/${slug}/findings?rule=${r.id}`}
                className="flex items-center justify-between text-sm py-2.5 px-3 rounded-lg hover:bg-gray-800/60 transition-colors group"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <StatusBadge value={r.severity} />
                  <span className="text-gray-300 font-mono text-xs truncate group-hover:text-white transition-colors">
                    {r.rule_id}
                  </span>
                </div>
                <span className="text-white font-bold text-sm ml-3 shrink-0">
                  {r.active_findings}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Recent Scans */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">Recent Scans</h2>
          <Link
            to={`/projects/${slug}/scans`}
            className="text-indigo-400 text-sm hover:underline"
          >
            View all
          </Link>
        </div>
        {recent_scans.length === 0 ? (
          <p className="text-gray-500 text-sm">
            No scans yet. Upload a Semgrep report to get started.
          </p>
        ) : (
          <div className="space-y-1">
            {recent_scans.map((s) => (
              <Link
                key={s.id}
                to={`/projects/${slug}/scans/${s.id}`}
                className="flex items-center justify-between text-sm py-2.5 px-3 border-b border-gray-800/50 last:border-0 hover:bg-gray-800/50 rounded-lg transition-colors"
              >
                <div className="flex items-center gap-2">
                  <svg
                    className="w-4 h-4 text-gray-500"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <span className="text-gray-400">
                    {new Date(s.scanned_at).toLocaleString()}
                  </span>
                </div>
                <div className="flex gap-3 text-xs">
                  <span className="text-blue-400">+{s.new_count} new</span>
                  <span className="text-orange-400">+{s.reopened_count} reopened</span>
                  <span className="text-green-400">-{s.resolved_count} resolved</span>
                  <span className="text-gray-500">{s.total_findings_count} total</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
