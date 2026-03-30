import { Link } from 'react-router-dom'
import StatusBadge from './StatusBadge'

function ChevronIcon({ expanded }) {
  return (
    <svg
      className={`w-4 h-4 text-gray-500 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={2}
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
    </svg>
  )
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-6">
      <svg className="animate-spin h-5 w-5 text-indigo-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>
  )
}

function groupFindingsByProject(findings) {
  const grouped = {}
  for (const f of findings) {
    const key = f.project_slug
    if (!grouped[key]) {
      grouped[key] = {
        slug: f.project_slug,
        name: f.project_name || f.project_slug,
        findings: [],
      }
    }
    grouped[key].findings.push(f)
  }
  return Object.values(grouped)
}

export default function RuleCard({ rule, expanded, findingsData, isLoading, onToggle }) {
  const findings = findingsData?.findings || []
  const findingsTotalCount = findingsData?.totalCount || 0
  const projectGroups = findings.length > 0 ? groupFindingsByProject(findings) : []

  return (
    <div
      className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden"
    >
      {/* Rule header - clickable to expand */}
      <button
        onClick={() => onToggle(rule.semgrep_rule_id)}
        className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-800/50 transition-colors text-left"
      >
        <div className="flex items-center gap-3 min-w-0">
          <StatusBadge value={rule.severity} />
          <div className="min-w-0">
            <p className="font-mono text-sm text-white truncate">{rule.semgrep_rule_id}</p>
            <p className="text-xs text-gray-500 truncate mt-0.5">{rule.message}</p>
          </div>
        </div>
        <div className="flex items-center gap-4 flex-shrink-0 ml-4">
          <div className="flex items-center gap-1">
            {/* Project dots */}
            <div className="flex -space-x-1 mr-1">
              {rule.projects?.slice(0, 4).map((p, i) => (
                <div
                  key={p.slug}
                  className="w-4 h-4 rounded-full border border-gray-900 flex items-center justify-center text-[8px] font-bold text-white"
                  style={{
                    backgroundColor: ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'][i % 5],
                    zIndex: 4 - i,
                  }}
                  title={p.name || p.slug}
                >
                  {(p.name || p.slug).charAt(0).toUpperCase()}
                </div>
              ))}
              {rule.projects?.length > 4 && (
                <div className="w-4 h-4 rounded-full border border-gray-900 bg-gray-700 flex items-center justify-center text-[7px] text-gray-300">
                  +{rule.projects.length - 4}
                </div>
              )}
            </div>
            <span className="text-xs text-gray-400">{rule.project_count} project{rule.project_count !== 1 ? 's' : ''}</span>
          </div>
          <span className="text-sm font-bold text-white">{rule.finding_count}</span>
          {rule.false_positive_count > 0 && (
            <span className="text-xs text-purple-400">{rule.false_positive_count} FP</span>
          )}
          <ChevronIcon expanded={expanded} />
        </div>
      </button>

      {/* Expanded content - findings grouped by project */}
      {expanded && (
        <div className="border-t border-gray-800 px-5 py-4">
          {isLoading ? (
            <LoadingSpinner />
          ) : projectGroups.length === 0 ? (
            <p className="text-gray-500 text-sm text-center py-4">No findings found for this rule.</p>
          ) : (
            <div className="space-y-4">
              {projectGroups.map(project => (
                <div key={project.slug}>
                  <div className="flex items-center gap-2 mb-2">
                    <Link
                      to={`/projects/${project.slug}`}
                      className="text-sm font-medium text-indigo-400 hover:underline"
                    >
                      {project.name}
                    </Link>
                    <span className="text-xs text-gray-500">
                      {project.findings.length} finding{project.findings.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <div className="ml-4 space-y-1">
                    {project.findings.map(f => (
                      <Link
                        key={f.id}
                        to={`/projects/${f.project_slug}/findings/${f.id}`}
                        className="flex items-center gap-3 py-1.5 px-3 rounded-lg hover:bg-gray-800 text-xs group transition-colors"
                      >
                        <span className="text-gray-400 font-mono truncate flex-1">
                          {f.file_path}:{f.line_start}
                        </span>
                        <StatusBadge value={f.status} />
                        {f.is_false_positive && (
                          <span className="text-purple-400 text-[10px] font-medium">FP</span>
                        )}
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
              {findingsTotalCount > findings.length && (
                <p className="text-xs text-gray-500 text-center pt-2">
                  Showing {findings.length} of {findingsTotalCount} findings
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
