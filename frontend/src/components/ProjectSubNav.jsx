import { Link, useParams, useLocation } from 'react-router-dom'

const tabs = [
  { label: 'Dashboard', path: '', exact: true },
  { label: 'Scans', path: '/scans' },
  { label: 'Findings', path: '/findings' },
  { label: 'Rules', path: '/rules' },
  { label: 'Members', path: '/members' },
  { label: 'Settings', path: '/settings' },
  { label: 'How To', path: '/how-to' },
]

export default function ProjectSubNav({ project }) {
  const { slug } = useParams()
  const location = useLocation()

  const basePath = `/projects/${slug}`

  function isActive(tab) {
    const fullPath = basePath + tab.path
    if (tab.exact) {
      return location.pathname === fullPath
    }
    return location.pathname.startsWith(fullPath)
  }

  return (
    <div className="bg-gray-900 border-b border-gray-800 px-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 pt-3 pb-2">
        <Link to="/" className="text-sm text-gray-400 hover:text-white transition-colors">
          Projects
        </Link>
        <span className="text-gray-600 text-sm">&gt;</span>
        <span className="text-sm text-white font-medium truncate">
          {project?.name || slug}
        </span>
      </div>

      {/* Tab links */}
      <div className="flex items-center gap-1 -mb-px">
        {tabs.map((tab) => {
          const active = isActive(tab)
          return (
            <Link
              key={tab.label}
              to={basePath + tab.path}
              className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
                active
                  ? 'text-indigo-400 border-indigo-400'
                  : 'text-gray-400 border-transparent hover:text-white hover:border-gray-600'
              }`}
            >
              {tab.label}
            </Link>
          )
        })}
      </div>
    </div>
  )
}
