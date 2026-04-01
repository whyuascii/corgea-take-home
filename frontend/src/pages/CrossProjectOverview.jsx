import { useEffect, useState, useMemo, useCallback } from 'react'
import api from '../api/client'
import { extractResults, getTotalPages } from '../api/helpers'
import Pagination from '../components/Pagination'
import RuleCard from '../components/RuleCard'
import PatternBanner from '../components/PatternBanner'
import useWebSocket from '../hooks/useWebSocket'

function StatCard({ label, value }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 flex items-center justify-between gap-3 min-w-0">
      <p className="text-gray-400 text-xs uppercase truncate">{label}</p>
      <p className="text-xl font-bold text-white">{value}</p>
    </div>
  )
}

const RULES_PAGE_SIZE = 25

export default function CrossProjectOverview() {
  const [rules, setRules] = useState([])
  const [rulesTotalCount, setRulesTotalCount] = useState(0)
  const [rulesPage, setRulesPage] = useState(1)
  const [summary, setSummary] = useState(null)
  const [severityFilter, setSeverityFilter] = useState('')
  const [projectFilter, setProjectFilter] = useState('')
  const [projects, setProjects] = useState([])
  const [expandedRules, setExpandedRules] = useState(new Set())
  const [ruleFindings, setRuleFindings] = useState({})
  const [loadingFindings, setLoadingFindings] = useState(new Set())
  const [loadingRules, setLoadingRules] = useState(true)

  const fetchSummary = useCallback(() => {
    api.get('/overview/summary/').then(r => setSummary(r.data))
  }, [])

  const handleWsMessage = useCallback((msg) => {
    if (msg.event === 'scan_complete') {
      fetchSummary()
      fetchRules()
    }
  }, [])

  useWebSocket('/ws/dashboard/', {
    onMessage: handleWsMessage,
  })

  useEffect(() => {
    fetchSummary()
  }, [])

  useEffect(() => {
    fetchRules()
  }, [severityFilter, rulesPage])

  // Reset page when severity filter changes
  useEffect(() => setRulesPage(1), [severityFilter])

  const fetchRules = async () => {
    setLoadingRules(true)
    try {
      const params = new URLSearchParams()
      params.set('page', rulesPage)
      if (severityFilter) params.set('severity', severityFilter)
      const { data } = await api.get(`/overview/rules/?${params}`)
      const parsed = extractResults(data)
      setRules(parsed.results)
      setRulesTotalCount(parsed.count)
      // Collect unique projects from rules data
      const projSet = new Map()
      parsed.results.forEach(r => r.projects?.forEach(p => projSet.set(p.slug, p.name)))
      setProjects(Array.from(projSet, ([slug, name]) => ({ slug, name })))
    } finally {
      setLoadingRules(false)
    }
  }

  // Sort rules: project count descending, then finding count descending
  const sortedRules = useMemo(() => {
    let filtered = [...rules]
    if (projectFilter) {
      filtered = filtered.filter(r =>
        r.projects?.some(p => p.slug === projectFilter)
      )
    }
    return filtered.sort((a, b) => {
      if (b.project_count !== a.project_count) return b.project_count - a.project_count
      return b.finding_count - a.finding_count
    })
  }, [rules, projectFilter])

  // Detect patterns: rules appearing in 3+ projects
  const patternsDetected = useMemo(() => {
    return sortedRules.filter(r => r.project_count >= 3)
  }, [sortedRules])

  const toggleRule = async (ruleId) => {
    const next = new Set(expandedRules)
    if (next.has(ruleId)) {
      next.delete(ruleId)
      setExpandedRules(next)
    } else {
      next.add(ruleId)
      setExpandedRules(next)
      // Fetch findings for this rule if not already loaded
      if (!ruleFindings[ruleId]) {
        setLoadingFindings(prev => new Set(prev).add(ruleId))
        try {
          const params = new URLSearchParams({ rule_id: ruleId })
          if (projectFilter) params.set('project', projectFilter)
          const { data } = await api.get(`/overview/findings/?${params}`)
          const parsed = extractResults(data)
          setRuleFindings(prev => ({ ...prev, [ruleId]: { findings: parsed.results, totalCount: parsed.count } }))
        } finally {
          setLoadingFindings(prev => {
            const s = new Set(prev)
            s.delete(ruleId)
            return s
          })
        }
      }
    }
  }

  const severities = ['', 'ERROR', 'WARNING', 'INFO']

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Cross-Project Overview</h1>

      {/* Summary Stats - compact single row */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <StatCard label="Total Findings" value={summary.total_findings} />
          <StatCard label="Active" value={summary.total_active} />
          <StatCard label="False Positives" value={summary.total_false_positives} />
          <StatCard label="Projects" value={summary.project_activity?.length || 0} />
        </div>
      )}

      {/* Pattern Detection Banner */}
      <PatternBanner patternsDetected={patternsDetected} onToggleRule={toggleRule} />

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <h2 className="text-lg font-semibold text-gray-300">Rules Across Projects</h2>
        <div className="flex flex-wrap gap-2 items-center">
          <select
            value={severityFilter}
            onChange={(e) => {
              setSeverityFilter(e.target.value)
              // Clear expanded state and cached findings when filters change
              setExpandedRules(new Set())
              setRuleFindings({})
            }}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">All Severities</option>
            {severities.slice(1).map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select
            value={projectFilter}
            onChange={(e) => {
              setProjectFilter(e.target.value)
              // Clear cached findings when project filter changes (findings are project-filtered)
              setRuleFindings({})
            }}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="">All Projects</option>
            {projects.map(p => <option key={p.slug} value={p.slug}>{p.name || p.slug}</option>)}
          </select>
          <span className="text-xs text-gray-500 ml-1">
            {sortedRules.length} rule{sortedRules.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Rule Cards - Main Content */}
      {loadingRules ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl px-5 py-4 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="h-5 w-16 bg-gray-800 rounded-full" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-800 rounded w-1/2" />
                  <div className="h-3 bg-gray-800 rounded w-3/4" />
                </div>
                <div className="h-4 w-8 bg-gray-800 rounded" />
              </div>
            </div>
          ))}
        </div>
      ) : sortedRules.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <p className="text-gray-500">No rules found matching the current filters.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sortedRules.map((rule) => (
            <RuleCard
              key={rule.semgrep_rule_id}
              rule={rule}
              expanded={expandedRules.has(rule.semgrep_rule_id)}
              findingsData={ruleFindings[rule.semgrep_rule_id]}
              isLoading={loadingFindings.has(rule.semgrep_rule_id)}
              onToggle={toggleRule}
            />
          ))}

          <Pagination page={rulesPage} totalPages={getTotalPages(rulesTotalCount, RULES_PAGE_SIZE)} onPageChange={setRulesPage} />
        </div>
      )}
    </div>
  )
}
