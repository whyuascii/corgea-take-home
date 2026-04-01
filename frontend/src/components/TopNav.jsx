import { useState, useEffect } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import api from '../api/client'
import UserDropdown from './UserDropdown'

function SearchBar({ slug }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    if (query.length < 2) { setResults([]); return }
    const timer = setTimeout(async () => {
      try {
        const { data } = await api.get(`/projects/${slug}/findings/search/?q=${encodeURIComponent(query)}`)
        setResults(data)
        setOpen(true)
      } catch {
        setResults([])
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query, slug])

  return (
    <div className="relative">
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length && setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 200)}
        placeholder="Search findings..."
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-gray-500 w-48 focus:w-64 transition-all focus:outline-none focus:border-indigo-500"
      />
      {open && results.length > 0 && (
        <div className="absolute top-full mt-1 w-80 bg-gray-900 border border-gray-700 rounded-lg shadow-xl z-50 max-h-64 overflow-y-auto">
          {results.slice(0, 10).map(f => (
            <button
              key={f.id}
              onMouseDown={() => { navigate(`/projects/${slug}/findings/${f.id}`); setOpen(false); setQuery('') }}
              className="w-full text-left px-3 py-2 hover:bg-gray-800 border-b border-gray-800 last:border-0"
            >
              <p className="text-xs font-mono text-indigo-400">{f.rule_id_display}</p>
              <p className="text-xs text-gray-400 truncate">{f.file_path}:{f.line_start}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function TopNav() {
  const { slug } = useParams()

  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
      {/* Left side: Logo + global nav */}
      <div className="flex items-center gap-6">
        <Link to="/" className="text-lg font-bold text-indigo-400">
          VulnTracker
        </Link>
        <Link
          to="/"
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          Projects
        </Link>
        <Link
          to="/overview"
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          Overview
        </Link>
      </div>

      {/* Right side: SearchBar (when in project) + UserDropdown */}
      <div className="flex items-center gap-4">
        {slug && <SearchBar slug={slug} />}
        <UserDropdown />
      </div>
    </nav>
  )
}
