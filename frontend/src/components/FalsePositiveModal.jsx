import { useState, useEffect } from 'react'

export default function FalsePositiveModal({ isOpen, onClose, onConfirm, isCurrentlyFP }) {
  const [reason, setReason] = useState('')
  const [applyToAll, setApplyToAll] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setReason('')
      setApplyToAll(false)
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleConfirm = async () => {
    setLoading(true)
    try {
      await onConfirm({
        is_false_positive: !isCurrentlyFP,
        reason,
        apply_to_all_projects: applyToAll,
      })
      setReason('')
      setApplyToAll(false)
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
        <h2 className="text-lg font-bold mb-4">
          {isCurrentlyFP ? 'Remove False Positive' : 'Mark as False Positive'}
        </h2>

        {!isCurrentlyFP && (
          <>
            <label className="block text-sm text-gray-400 mb-1">Reason (optional)</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g., Test file, not production code"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white mb-4 resize-none"
              rows={3}
            />

            <label className="flex items-center gap-2 text-sm text-gray-300 mb-4 cursor-pointer">
              <input
                type="checkbox"
                checked={applyToAll}
                onChange={(e) => setApplyToAll(e.target.checked)}
                className="rounded border-gray-600 bg-gray-800 text-indigo-600 focus:ring-indigo-500"
              />
              Apply to all projects with the same rule
            </label>
          </>
        )}

        {isCurrentlyFP && (
          <p className="text-sm text-gray-400 mb-4">
            This will remove the false positive mark and allow the finding to resume normal lifecycle.
          </p>
        )}

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded text-sm"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded text-sm disabled:opacity-50"
          >
            {loading ? 'Saving...' : isCurrentlyFP ? 'Remove FP' : 'Mark as FP'}
          </button>
        </div>
      </div>
    </div>
  )
}
