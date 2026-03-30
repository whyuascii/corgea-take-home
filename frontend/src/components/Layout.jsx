import { useState, useEffect } from 'react'
import { Link, Outlet, useParams, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'

function SearchBar({ slug }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    if (query.length < 2) { setResults([]); return }
    const timer = setTimeout(async () => {
      const { data } = await api.get(`/projects/${slug}/findings/search/?q=${encodeURIComponent(query)}`)
      setResults(data)
      setOpen(true)
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

export default function Layout() {
  const { slug } = useParams()
  const { user, logout } = useAuth()
  const location = useLocation()

  const navLinks = slug
    ? [
        { to: `/projects/${slug}`, label: 'Dashboard', exact: true },
        { to: `/projects/${slug}/scans`, label: 'Scans' },
        { to: `/projects/${slug}/findings`, label: 'Findings' },
        { to: `/projects/${slug}/rules`, label: 'Rules' },
        { to: `/projects/${slug}/settings`, label: 'Settings' },
        { to: `/projects/${slug}/how-to`, label: 'How To' },
      ]
    : [
        { to: '/', label: 'Projects', exact: true },
        { to: '/overview', label: 'Overview' },
        { to: '/how-to', label: 'How To' },
      ]

  const isActive = (link) => {
    if (link.exact) return location.pathname === link.to
    return location.pathname.startsWith(link.to)
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link to="/" className="text-lg font-bold text-indigo-400">VulnTracker</Link>
          {navLinks.map((link) => (
            <Link key={link.to} to={link.to}
              className={`text-sm ${isActive(link) ? 'text-white' : 'text-gray-400 hover:text-white'}`}>
              {link.label}
            </Link>
          ))}
        </div>
        <div className="flex items-center gap-4">
          {slug && <SearchBar slug={slug} />}
          <span className="text-sm text-gray-400">{user?.username}</span>
          <button onClick={logout} className="text-sm text-gray-400 hover:text-white">Logout</button>
        </div>
      </nav>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
