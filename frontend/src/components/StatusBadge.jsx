const colors = {
  new:            'bg-blue-500/20 text-blue-400',
  open:           'bg-yellow-500/20 text-yellow-400',
  reopened:       'bg-orange-500/20 text-orange-400',
  resolved:       'bg-green-500/20 text-green-400',
  ignored:        'bg-gray-500/20 text-gray-400',
  false_positive: 'bg-purple-500/20 text-purple-400',
  active:         'bg-green-500/20 text-green-400',
  ERROR:          'bg-red-500/20 text-red-400',
  WARNING:        'bg-yellow-500/20 text-yellow-400',
  INFO:           'bg-blue-500/20 text-blue-400',
  LOW:            'bg-green-500/20 text-green-400',
  MEDIUM:         'bg-yellow-500/20 text-yellow-400',
  HIGH:           'bg-red-500/20 text-red-400',
}

const labels = {
  ERROR: 'Critical',
  WARNING: 'Warning',
  INFO: 'Info',
  false_positive: 'False Positive',
}

export default function StatusBadge({ value }) {
  if (!value) return null
  const displayLabel = labels[value] || value.charAt(0).toUpperCase() + value.slice(1)
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${colors[value] || 'bg-gray-700 text-gray-300'}`}>
      {displayLabel}
    </span>
  )
}
