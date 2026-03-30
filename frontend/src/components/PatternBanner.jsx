import StatusBadge from './StatusBadge'

export default function PatternBanner({ patternsDetected, onToggleRule }) {
  if (patternsDetected.length === 0) return null

  return (
    <div className="bg-orange-500/10 border border-orange-500/20 rounded-xl p-4 mb-6">
      <h3 className="text-sm font-medium text-orange-400 mb-2">
        Recurring Patterns Detected
      </h3>
      <p className="text-xs text-gray-400 mb-2">
        These coding issues appear across multiple projects:
      </p>
      <div className="space-y-1">
        {patternsDetected.map(r => (
          <button
            key={r.semgrep_rule_id}
            onClick={() => onToggleRule(r.semgrep_rule_id)}
            className="flex items-center gap-2 text-xs w-full hover:bg-orange-500/5 rounded px-1 py-0.5 transition-colors text-left"
          >
            <StatusBadge value={r.severity} />
            <span className="text-gray-300 font-mono truncate">{r.semgrep_rule_id}</span>
            <span className="text-orange-400 ml-auto flex-shrink-0">{r.project_count} projects</span>
          </button>
        ))}
      </div>
    </div>
  )
}
