export function SkeletonCard() {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 animate-pulse">
      <div className="h-3 bg-gray-800 rounded w-1/3 mb-3" />
      <div className="h-6 bg-gray-800 rounded w-1/2" />
    </div>
  )
}
