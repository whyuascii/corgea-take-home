import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'
import { extractResults, getTotalPages } from '../api/helpers'
import StatusBadge from '../components/StatusBadge'
import Pagination from '../components/Pagination'
import FindingsToolbar from '../components/FindingsToolbar'
import BulkActionsBar from '../components/BulkActionsBar'

const PAGE_SIZE = 25

export default function FindingsList() {
  const { slug } = useParams()
  const [findings, setFindings] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState('active') // 'active' | 'fp_only' | 'all'
  const [statusFilter, setStatusFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [bulkStatus, setBulkStatus] = useState('open')
  const [bulkLoading, setBulkLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [actionOpen, setActionOpen] = useState(null)
  const actionRef = useRef(null)

  useEffect(() => { fetchFindings() }, [slug, viewMode, statusFilter, severityFilter, page])

  // Reset page when filters change
  useEffect(() => setPage(1), [viewMode, statusFilter, severityFilter])

  // Close action dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (actionRef.current && !actionRef.current.contains(e.target)) {
        setActionOpen(null)
      }
    }
    if (actionOpen !== null) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [actionOpen])

  const fetchFindings = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.set('page', page)
      if (viewMode === 'fp_only') params.set('is_false_positive', 'true')
      else if (viewMode === 'all') params.set('show_all', 'true')
      // 'active' mode: no param, backend excludes FP by default
      if (statusFilter) params.set('status', statusFilter)
      if (severityFilter) params.set('severity', severityFilter)
      const { data } = await api.get(`/projects/${slug}/findings/?${params}`)
      const parsed = extractResults(data)
      setFindings(parsed.results)
      setTotalCount(parsed.count)
      setSelectedIds(new Set())
    } catch (err) {
      console.error('Failed to fetch findings:', err)
    } finally {
      setLoading(false)
    }
  }

  const totalPages = getTotalPages(totalCount, PAGE_SIZE)

  const handleExport = async () => {
    try {
      const params = new URLSearchParams()
      if (viewMode === 'fp_only') params.set('is_false_positive', 'true')
      else if (viewMode === 'all') params.set('show_all', 'true')
      if (statusFilter) params.set('status', statusFilter)
      if (severityFilter) params.set('severity', severityFilter)
      const query = params.toString() ? `?${params}` : ''
      const { data } = await api.get(`/projects/${slug}/findings/export/${query}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `findings-${slug}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to export findings:', err)
    }
  }

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleSelectAll = () => {
    if (findings.length > 0 && selectedIds.size === findings.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(findings.map((f) => f.id)))
    }
  }

  const handleBulkStatusChange = async () => {
    if (selectedIds.size === 0) return
    setBulkLoading(true)
    try {
      await api.post(`/projects/${slug}/findings/bulk/`, {
        finding_ids: Array.from(selectedIds),
        action: 'status_change',
        status: bulkStatus,
      })
      await fetchFindings()
    } catch (err) {
      console.error('Bulk status change failed:', err)
    } finally {
      setBulkLoading(false)
    }
  }

  const handleBulkFP = async () => {
    if (selectedIds.size === 0) return
    setBulkLoading(true)
    try {
      await api.post(`/projects/${slug}/findings/bulk/`, {
        finding_ids: Array.from(selectedIds),
        action: 'false_positive',
        is_false_positive: true,
        reason: 'Bulk marked as false positive',
      })
      await fetchFindings()
    } catch (err) {
      console.error('Bulk false positive marking failed:', err)
    } finally {
      setBulkLoading(false)
    }
  }

  const handleQuickStatus = async (findingId, newStatus) => {
    try {
      await api.patch(`/projects/${slug}/findings/${findingId}/`, { status: newStatus })
      setActionOpen(null)
      fetchFindings()
    } catch (err) {
      console.error('Status change failed:', err)
    }
  }

  const viewModeLabel = {
    active: 'active',
    fp_only: 'false positive',
    all: '',
  }

  const reopenedCount = findings.filter(f => f.status === 'reopened').length

  const summaryText = () => {
    const total = totalCount
    const label = viewModeLabel[viewMode]
    if (label) {
      return `${total} ${label} finding${total !== 1 ? 's' : ''}`
    }
    return `${total} finding${total !== 1 ? 's' : ''}`
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Findings</h1>
        <p className="text-sm text-gray-400">
          {loading ? 'Loading...' : summaryText()}
        </p>
      </div>

      {/* Filter toolbar */}
      <FindingsToolbar
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        severityFilter={severityFilter}
        onSeverityFilterChange={setSeverityFilter}
        onExport={handleExport}
        reopenedCount={reopenedCount}
      />

      {/* Bulk actions bar */}
      <BulkActionsBar
        selectedCount={selectedIds.size}
        bulkStatus={bulkStatus}
        onBulkStatusChange={setBulkStatus}
        onBulkStatusSubmit={handleBulkStatusChange}
        onBulkFP={handleBulkFP}
        onClearSelection={() => setSelectedIds(new Set())}
        bulkLoading={bulkLoading}
      />

      {/* Findings table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-800/50">
              <tr>
                <th className="px-4 py-3 w-8">
                  <input
                    type="checkbox"
                    checked={findings.length > 0 && selectedIds.size === findings.length}
                    onChange={toggleSelectAll}
                    className="rounded border-gray-600 bg-gray-800 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-0"
                  />
                </th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Rule</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">File</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Line</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Severity</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Status</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Last Seen</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider w-10"></th>
              </tr>
            </thead>
            <tbody>
              {!loading && findings.map((f) => (
                <tr key={f.id} className={`border-t border-gray-800 hover:bg-gray-800/30 group ${selectedIds.has(f.id) ? 'bg-indigo-500/5' : ''}`}>
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(f.id)}
                      onChange={() => toggleSelect(f.id)}
                      className="rounded border-gray-600 bg-gray-800 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-0"
                    />
                  </td>
                  <td className="px-4 py-3 font-mono text-xs max-w-[200px]">
                    <Link to={`/projects/${slug}/findings/${f.id}`} className="text-indigo-400 hover:underline truncate block" title={f.rule_id_display}>
                      {f.rule_id_display}
                    </Link>
                    {f.is_false_positive && <span className="ml-0 mt-1 inline-block px-1.5 py-0.5 rounded-full text-[10px] bg-purple-500/20 text-purple-400">FP</span>}
                  </td>
                  <td className="px-4 py-3 text-gray-300 font-mono text-xs max-w-[250px] truncate" title={f.file_path}>
                    {f.file_path}
                  </td>
                  <td className="px-4 py-3 text-gray-400">{f.line_start}-{f.line_end}</td>
                  <td className="px-4 py-3"><StatusBadge value={f.severity} /></td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <StatusBadge value={f.status} />
                      {f.status === 'reopened' && (
                        <span
                          className="inline-flex items-center gap-1 text-[10px] text-orange-400"
                          title={`Reopened on ${new Date(f.updated_at).toLocaleString()}`}
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-orange-400 inline-block shrink-0"></span>
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                    {f.status === 'reopened' ? (
                      <span className="text-orange-400" title={`Reopened: ${new Date(f.updated_at).toLocaleString()}`}>
                        {new Date(f.updated_at).toLocaleDateString()}
                      </span>
                    ) : (
                      new Date(f.updated_at).toLocaleDateString()
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="relative" ref={actionOpen === f.id ? actionRef : undefined}>
                      <button
                        onClick={() => setActionOpen(actionOpen === f.id ? null : f.id)}
                        className="text-gray-600 hover:text-gray-300 opacity-0 group-hover:opacity-100 focus:opacity-100 p-1 rounded transition-opacity"
                        title="Actions"
                      >
                        &#8942;
                      </button>
                      {actionOpen === f.id && (
                        <div className="absolute right-0 top-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-10 py-1 min-w-[140px]">
                          {['new', 'open', 'resolved', 'ignored'].map(s => (
                            <button key={s} onClick={() => handleQuickStatus(f.id, s)}
                              className="w-full text-left px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-700 transition-colors">
                              Set {s.charAt(0).toUpperCase() + s.slice(1)}
                            </button>
                          ))}
                          {f.status === 'ignored' && (
                            <button onClick={() => handleQuickStatus(f.id, 'reopened')}
                              className="w-full text-left px-3 py-1.5 text-xs text-orange-400 hover:bg-gray-700 border-t border-gray-700 transition-colors">
                              Unignore
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-6 w-6 border-2 border-gray-600 border-t-indigo-500"></div>
              <span className="ml-3 text-gray-400 text-sm">Loading findings...</span>
            </div>
          )}
          {!loading && findings.length === 0 && <p className="text-gray-500 text-center py-8">No findings match</p>}
        </div>
      </div>

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
    </div>
  )
}
