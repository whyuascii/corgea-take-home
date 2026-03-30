export default function Pagination({ page, totalPages, onPageChange }) {
  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-center gap-2 mt-4">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-sm disabled:opacity-30 disabled:hover:bg-gray-800"
      >
        Previous
      </button>
      <span className="text-sm text-gray-400">
        Page {page} of {totalPages}
      </span>
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded text-sm disabled:opacity-30 disabled:hover:bg-gray-800"
      >
        Next
      </button>
    </div>
  )
}
