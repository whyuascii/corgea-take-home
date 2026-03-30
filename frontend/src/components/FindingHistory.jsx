import StatusBadge from './StatusBadge'

export default function FindingHistory({ historyItems, historyExpanded, onToggleExpanded }) {
  const visibleHistory = historyExpanded ? historyItems : historyItems.slice(0, 5)

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">History</h3>
      {historyItems.length === 0 ? (
        <p className="text-gray-600 text-xs">No history yet</p>
      ) : (
        <div className="space-y-3">
          {visibleHistory.map((h) => (
            <div key={h.id} className="flex gap-2.5 text-xs">
              <div className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${
                h.change_type === 'false_positive' ? 'bg-purple-500' : 'bg-indigo-500'
              }`} />
              <div className="min-w-0 flex-1">
                {h.change_type === 'false_positive' ? (
                  <p className="text-purple-400 leading-snug">
                    {h.notes}
                    {h.changed_by_username && <span className="text-gray-600 ml-1">by {h.changed_by_username}</span>}
                  </p>
                ) : (
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <StatusBadge value={h.old_status || '(created)'} />
                    <span className="text-gray-600">&rarr;</span>
                    <StatusBadge value={h.new_status} />
                    {h.changed_by_username && <span className="text-gray-600">by {h.changed_by_username}</span>}
                  </div>
                )}
                <p className="text-gray-600 mt-0.5">{new Date(h.created_at).toLocaleString()}</p>
                {h.change_type !== 'false_positive' && h.notes && <p className="text-gray-500 mt-0.5">{h.notes}</p>}
              </div>
            </div>
          ))}
          {historyItems.length > 5 && (
            <button
              onClick={onToggleExpanded}
              className="text-indigo-400 hover:text-indigo-300 text-xs font-medium transition-colors"
            >
              {historyExpanded ? 'Show less' : `Show all (${historyItems.length})`}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
