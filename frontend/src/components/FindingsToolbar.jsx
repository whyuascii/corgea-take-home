export default function FindingsToolbar({
  viewMode,
  onViewModeChange,
  statusFilter,
  onStatusFilterChange,
  severityFilter,
  onSeverityFilterChange,
  onExport,
  reopenedCount = 0,
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-3 mb-4 flex flex-wrap items-center gap-3">
      {/* View mode toggle (segmented control) */}
      <div className="flex bg-gray-800 rounded-lg p-0.5">
        {[
          { key: 'active', label: 'Active' },
          { key: 'all', label: 'All' },
          { key: 'fp_only', label: 'False Positives' },
        ].map(mode => (
          <button key={mode.key} onClick={() => onViewModeChange(mode.key)}
            className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
              viewMode === mode.key ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'
            }`}>
            {mode.label}
          </button>
        ))}
      </div>

      {/* Reopened count indicator (only in active view) */}
      {viewMode === 'active' && reopenedCount > 0 && (
        <button
          onClick={() => onStatusFilterChange(statusFilter === 'reopened' ? '' : 'reopened')}
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
            statusFilter === 'reopened'
              ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30'
              : 'bg-orange-500/10 text-orange-400 hover:bg-orange-500/20 border border-transparent'
          }`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-orange-400 inline-block"></span>
          {reopenedCount} reopened
        </button>
      )}

      {/* Status filter dropdown */}
      <select value={statusFilter} onChange={(e) => onStatusFilterChange(e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-gray-300">
        <option value="">All Statuses</option>
        <option value="new">New</option>
        <option value="open">Open</option>
        <option value="reopened">Reopened</option>
        <option value="resolved">Resolved</option>
        <option value="ignored">Ignored</option>
      </select>

      {/* Severity filter dropdown */}
      <select value={severityFilter} onChange={(e) => onSeverityFilterChange(e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-gray-300">
        <option value="">All Severities</option>
        <option value="ERROR">Critical</option>
        <option value="WARNING">Warning</option>
        <option value="INFO">Info</option>
      </select>

      {/* Spacer + export */}
      <div className="ml-auto">
        <button onClick={onExport} className="px-3 py-1.5 bg-gray-800 border border-gray-700 text-gray-400 hover:text-white rounded-lg text-xs">
          Export CSV
        </button>
      </div>
    </div>
  )
}
