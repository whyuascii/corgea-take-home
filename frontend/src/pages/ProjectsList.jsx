import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { extractResults, getTotalPages } from '../api/helpers'
import Pagination from '../components/Pagination'

function timeAgo(dateStr) {
  if (!dateStr) return 'Never'
  const now = new Date()
  const date = new Date(dateStr)
  const seconds = Math.floor((now - date) / 1000)
  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`
  return date.toLocaleDateString()
}

function getHealthColor(critical) {
  if (!critical || critical === 0) return 'border-l-green-500'
  if (critical <= 5) return 'border-l-yellow-500'
  return 'border-l-red-500'
}

function getHealthDot(critical) {
  if (!critical || critical === 0) return 'bg-green-500'
  if (critical <= 5) return 'bg-yellow-500'
  return 'bg-red-500'
}

function getHealthLabel(critical) {
  if (!critical || critical === 0) return 'Healthy'
  if (critical <= 5) return 'Warning'
  return 'Critical'
}

function SkeletonCard() {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 animate-pulse border-l-4 border-l-gray-800">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="h-5 bg-gray-800 rounded w-3/4 mb-2" />
          <div className="h-3 bg-gray-800 rounded w-1/2" />
        </div>
        <div className="h-8 w-8 bg-gray-800 rounded-full" />
      </div>
      <div className="h-2 bg-gray-800 rounded-full w-full mb-4" />
      <div className="flex gap-2 mb-3">
        <div className="h-5 bg-gray-800 rounded-full w-16" />
        <div className="h-5 bg-gray-800 rounded-full w-16" />
        <div className="h-5 bg-gray-800 rounded-full w-16" />
      </div>
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-800">
        <div className="h-3 bg-gray-800 rounded w-20" />
        <div className="h-3 bg-gray-800 rounded w-24" />
      </div>
    </div>
  )
}

function DistributionBar({ summary }) {
  const { total } = summary
  if (!total || total === 0) {
    return (
      <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div className="h-full bg-gray-700 rounded-full" style={{ width: '100%' }} />
      </div>
    )
  }

  const newPct = (summary.new / total) * 100
  const openPct = (summary.open / total) * 100
  const reopenedPct = (summary.reopened / total) * 100
  const resolvedPct = (summary.resolved / total) * 100
  const ignoredPct = (summary.ignored / total) * 100
  const fpPct = (summary.false_positive / total) * 100

  return (
    <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden flex">
      {newPct > 0 && (
        <div
          className="h-full bg-blue-500"
          style={{ width: `${newPct}%` }}
          title={`New: ${summary.new}`}
        />
      )}
      {openPct > 0 && (
        <div
          className="h-full bg-yellow-500"
          style={{ width: `${openPct}%` }}
          title={`Open: ${summary.open}`}
        />
      )}
      {reopenedPct > 0 && (
        <div
          className="h-full bg-orange-500"
          style={{ width: `${reopenedPct}%` }}
          title={`Reopened: ${summary.reopened}`}
        />
      )}
      {resolvedPct > 0 && (
        <div
          className="h-full bg-green-500"
          style={{ width: `${resolvedPct}%` }}
          title={`Resolved: ${summary.resolved}`}
        />
      )}
      {ignoredPct > 0 && (
        <div
          className="h-full bg-gray-500"
          style={{ width: `${ignoredPct}%` }}
          title={`Ignored: ${summary.ignored}`}
        />
      )}
      {fpPct > 0 && (
        <div
          className="h-full bg-gray-600"
          style={{ width: `${fpPct}%` }}
          title={`False Positive: ${summary.false_positive}`}
        />
      )}
    </div>
  )
}

function ProjectCard({ project }) {
  const summary = project.findings_summary || {}
  const critical = summary.critical || 0
  const total = summary.total || 0
  const active = (summary.new || 0) + (summary.open || 0) + (summary.reopened || 0)
  const healthColor = getHealthColor(critical)
  const healthDot = getHealthDot(critical)
  const healthLabel = getHealthLabel(critical)

  return (
    <Link
      to={`/projects/${project.slug}`}
      className={`group block bg-gray-900 border border-gray-800 border-l-4 ${healthColor} rounded-xl p-5 hover:border-indigo-500 hover:border-l-indigo-500 transition-all duration-200 hover:shadow-lg hover:shadow-indigo-500/5`}
    >
      {/* Header row */}
      <div className="flex items-start justify-between mb-1">
        <h2 className="text-lg font-bold text-white group-hover:text-indigo-400 transition-colors truncate pr-3">
          {project.name}
        </h2>
        <div className="flex-shrink-0 flex items-center gap-1.5" title={`${critical} critical finding${critical !== 1 ? 's' : ''}`}>
          <span className={`inline-block w-2.5 h-2.5 rounded-full ${healthDot}`} />
          <span className="text-xs text-gray-500">{healthLabel}</span>
        </div>
      </div>

      {/* Repository URL */}
      {project.repository_url ? (
        <p className="text-xs text-gray-500 truncate mb-3" title={project.repository_url}>
          {project.repository_url.replace(/^https?:\/\//, '')}
        </p>
      ) : (
        <p className="text-xs text-gray-600 mb-3 italic">No repository linked</p>
      )}

      {/* Distribution bar */}
      <DistributionBar summary={summary} />

      {/* Bar legend */}
      <div className="flex items-center gap-3 mt-2 text-[10px] text-gray-500">
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-sm bg-blue-500" />
          New
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-sm bg-yellow-500" />
          Open
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-sm bg-green-500" />
          Resolved
        </span>
      </div>

      {/* Stats badges */}
      <div className="flex flex-wrap items-center gap-2 mt-3">
        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-800 rounded-full text-xs text-gray-300 font-medium">
          <svg className="w-3 h-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {total} total
        </span>

        {active > 0 && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-indigo-500/15 text-indigo-400 rounded-full text-xs font-medium">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            {active} active
          </span>
        )}

        {critical > 0 && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-500/15 text-red-400 rounded-full text-xs font-medium">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.618 5.984A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            {critical} critical
          </span>
        )}
      </div>

      {/* Footer: last scan time */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-800/60">
        <span className="text-[11px] text-gray-500 flex items-center gap-1">
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Last scan: {timeAgo(summary.last_scan_at)}
        </span>
        <span className="text-[11px] text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
          View project
          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </span>
      </div>
    </Link>
  )
}

function EmptyState({ onCreateClick }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="w-20 h-20 mb-6 rounded-2xl bg-gray-900 border border-gray-800 flex items-center justify-center">
        <svg className="w-10 h-10 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
        </svg>
      </div>
      <h3 className="text-xl font-semibold text-white mb-2">No projects yet</h3>
      <p className="text-gray-500 text-sm mb-6 text-center max-w-sm">
        Create your first project to start tracking security vulnerabilities across your codebase.
      </p>
      <button
        onClick={onCreateClick}
        className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Create your first project
      </button>
    </div>
  )
}

const PAGE_SIZE = 25

export default function ProjectsList() {
  const [projects, setProjects] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [repoUrl, setRepoUrl] = useState('')
  const [creating, setCreating] = useState(false)
  const [page, setPage] = useState(1)

  useEffect(() => { fetchProjects() }, [page])

  const fetchProjects = async () => {
    setLoading(true)
    try {
      const { data } = await api.get(`/projects/?page=${page}`)
      const parsed = extractResults(data)
      setProjects(parsed.results)
      setTotalCount(parsed.count)
    } catch {
      setError('Failed to load projects')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreating(true)
    setError(null)
    try {
      await api.post('/projects/', { name, repository_url: repoUrl })
      setName('')
      setRepoUrl('')
      setShowCreate(false)
      fetchProjects()
    } catch {
      setError('Failed to create project')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div>
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Projects</h1>
          {!loading && totalCount > 0 && (
            <p className="text-sm text-gray-500 mt-1">
              {totalCount} project{totalCount !== 1 ? 's' : ''} tracked
            </p>
          )}
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
        >
          {showCreate ? (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
              Cancel
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              New Project
            </>
          )}
        </button>
      </div>

      {/* Create form with slide-down animation */}
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          showCreate ? 'max-h-80 opacity-100 mb-8' : 'max-h-0 opacity-0 mb-0'
        }`}
      >
        <form
          onSubmit={handleCreate}
          className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4"
        >
          <div>
            <h3 className="text-sm font-semibold text-white mb-3">Create a new project</h3>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">Project name *</label>
              <input
                type="text"
                placeholder="e.g. My Application"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 transition-colors placeholder-gray-600"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">Repository URL</label>
              <input
                type="url"
                placeholder="https://github.com/org/repo"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 transition-colors placeholder-gray-600"
              />
            </div>
          </div>
          <div className="flex items-center gap-3 pt-1">
            <button
              type="submit"
              disabled={creating}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors"
            >
              {creating ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Creating...
                </>
              ) : (
                'Create project'
              )}
            </button>
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="mb-4 px-4 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Loading state: skeleton cards */}
      {loading && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      )}

      {/* Project grid */}
      {!loading && projects.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => (
            <ProjectCard key={p.id} project={p} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && projects.length === 0 && !showCreate && (
        <EmptyState onCreateClick={() => setShowCreate(true)} />
      )}

      <Pagination page={page} totalPages={getTotalPages(totalCount, PAGE_SIZE)} onPageChange={setPage} />
    </div>
  )
}
