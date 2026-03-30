export default function BulkActionsBar({
  selectedCount,
  bulkStatus,
  onBulkStatusChange,
  onBulkStatusSubmit,
  onBulkFP,
  onClearSelection,
  bulkLoading,
}) {
  if (selectedCount === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-3 mb-4 bg-gray-900 border border-gray-700 rounded-xl px-4 py-3">
      <span className="text-sm text-gray-300">{selectedCount} selected</span>
      <div className="flex items-center gap-2 ml-4">
        <select
          value={bulkStatus}
          onChange={(e) => onBulkStatusChange(e.target.value)}
          className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
        >
          {['new', 'open', 'reopened', 'resolved', 'ignored'].map((s) => (
            <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>
        <button
          onClick={onBulkStatusSubmit}
          disabled={bulkLoading}
          className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 rounded text-xs text-white font-medium disabled:opacity-50"
        >
          Change Status
        </button>
      </div>
      <button
        onClick={onBulkFP}
        disabled={bulkLoading}
        className="px-3 py-1 bg-purple-600 hover:bg-purple-700 rounded text-xs text-white font-medium disabled:opacity-50"
      >
        Mark as FP
      </button>
      <button
        onClick={onClearSelection}
        className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs text-gray-300 font-medium ml-auto"
      >
        Clear selection
      </button>
    </div>
  )
}
