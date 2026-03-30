import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client'
import { extractResults } from '../api/helpers'
import StatusBadge from '../components/StatusBadge'

export default function RulesList() {
  const { slug } = useParams()
  const [activeRules, setActiveRules] = useState([])
  const [ignoredRules, setIgnoredRules] = useState([])
  const [loadingActive, setLoadingActive] = useState(true)
  const [loadingIgnored, setLoadingIgnored] = useState(true)
  const [ignoredExpanded, setIgnoredExpanded] = useState(false)

  useEffect(() => {
    fetchActiveRules()
    fetchIgnoredRules()
  }, [slug])

  const fetchActiveRules = async () => {
    setLoadingActive(true)
    try {
      const { data } = await api.get(`/projects/${slug}/findings/rules/?status=active`)
      const parsed = extractResults(data)
      const sorted = [...parsed.results].sort(
        (a, b) => (b.active_finding_count || 0) - (a.active_finding_count || 0)
      )
      setActiveRules(sorted)
    } catch (err) {
      console.error('Failed to fetch active rules:', err)
    } finally {
      setLoadingActive(false)
    }
  }

  const fetchIgnoredRules = async () => {
    setLoadingIgnored(true)
    try {
      const { data } = await api.get(`/projects/${slug}/findings/rules/?status=ignored`)
      const parsed = extractResults(data)
      setIgnoredRules(parsed.results)
    } catch (err) {
      console.error('Failed to fetch ignored rules:', err)
    } finally {
      setLoadingIgnored(false)
    }
  }

  const toggleIgnore = async (rule) => {
    const newStatus = rule.status === 'active' ? 'ignored' : 'active'
    try {
      await api.patch(`/projects/${slug}/findings/rules/${rule.id}/`, { status: newStatus })
      fetchActiveRules()
      fetchIgnoredRules()
    } catch (err) {
      console.error('Failed to toggle rule status:', err)
    }
  }

  const hasReopenedFindings = (rule) => {
    return rule.has_reopened_findings === true
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Rules</h1>

      {/* Active Rules Section */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-3">
          <h2 className="text-lg font-semibold text-gray-200">Active Rules</h2>
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-500/20 text-indigo-400">
            {loadingActive ? '...' : activeRules.length}
          </span>
        </div>
        <RulesTable
          rules={activeRules}
          loading={loadingActive}
          onToggle={toggleIgnore}
          isActive={true}
          hasReopenedFindings={hasReopenedFindings}
          emptyMessage="No active rules"
        />
      </div>

      {/* Ignored Rules Section */}
      <div>
        <button
          onClick={() => setIgnoredExpanded(!ignoredExpanded)}
          className="flex items-center gap-3 mb-3 group"
        >
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${ignoredExpanded ? 'rotate-90' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
          <h2 className="text-lg font-semibold text-gray-400 group-hover:text-gray-300 transition-colors">
            Ignored Rules
          </h2>
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-500/20 text-gray-400">
            {loadingIgnored ? '...' : ignoredRules.length}
          </span>
        </button>

        {ignoredExpanded && (
          <RulesTable
            rules={ignoredRules}
            loading={loadingIgnored}
            onToggle={toggleIgnore}
            isActive={false}
            hasReopenedFindings={hasReopenedFindings}
            emptyMessage="No ignored rules"
          />
        )}
      </div>
    </div>
  )
}

function RulesTable({ rules, loading, onToggle, isActive, hasReopenedFindings, emptyMessage }) {
  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-xl overflow-hidden ${!isActive ? 'opacity-70' : ''}`}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Rule ID</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Severity</th>
              <th className="text-right px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Active Findings</th>
              <th className="text-right px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Total Findings</th>
              <th className="text-right px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Action</th>
            </tr>
          </thead>
          <tbody>
            {!loading && rules.map((r) => (
              <tr key={r.id} className="border-t border-gray-800 hover:bg-gray-800/30">
                <td className="px-4 py-3 max-w-[300px]">
                  <div className="flex items-center gap-2">
                    <div className="font-mono text-xs text-gray-300 truncate" title={r.semgrep_rule_id}>
                      {r.semgrep_rule_id}
                    </div>
                    {hasReopenedFindings(r) && (
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-orange-500/20 text-orange-400 whitespace-nowrap shrink-0">
                        reopened
                      </span>
                    )}
                  </div>
                  {r.message && (
                    <div className="text-[11px] text-gray-500 truncate mt-0.5 max-w-[300px]" title={r.message}>
                      {r.message}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3"><StatusBadge value={r.severity} /></td>
                <td className="px-4 py-3 text-right tabular-nums">
                  <span className="font-bold text-gray-200">{r.active_finding_count ?? r.finding_count ?? 0}</span>
                </td>
                <td className="px-4 py-3 text-right tabular-nums">
                  <span className="text-gray-500 text-xs">{r.total_finding_count ?? r.finding_count ?? 0}</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => onToggle(r)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-gray-700 hover:bg-gray-600 text-gray-300 border border-gray-600'
                        : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                    }`}
                  >
                    {isActive ? 'Ignore' : 'Reactivate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-gray-600 border-t-indigo-500"></div>
            <span className="ml-3 text-gray-400 text-sm">Loading rules...</span>
          </div>
        )}
        {!loading && rules.length === 0 && (
          <p className="text-gray-500 text-center py-8">{emptyMessage}</p>
        )}
      </div>
    </div>
  )
}
