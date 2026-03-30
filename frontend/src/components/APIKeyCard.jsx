import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'

export default function APIKeyCard({ projectSlug }) {
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showKey, setShowKey] = useState(false)
  const [regenerating, setRegenerating] = useState(false)

  const fetchProject = useCallback(async () => {
    try {
      const { data } = await api.get(`/projects/${projectSlug}/`)
      setProject(data)
    } catch (err) {
      console.error('Failed to load project', err)
    } finally {
      setLoading(false)
    }
  }, [projectSlug])

  useEffect(() => { fetchProject() }, [fetchProject])

  const handleCopy = () => {
    if (project?.api_key) {
      navigator.clipboard.writeText(project.api_key)
    }
  }

  const handleRegenerate = async () => {
    if (!window.confirm('This will invalidate the existing key. Any CI/CD pipelines using the current key will stop working. Are you sure?')) {
      return
    }
    setRegenerating(true)
    try {
      await api.post(`/projects/${projectSlug}/regenerate_api_key/`)
      setShowKey(false)
      await fetchProject()
    } catch (err) {
      alert('Failed to regenerate API key: ' + (err.response?.data?.detail || err.message))
    } finally {
      setRegenerating(false)
    }
  }

  const formatLastUsed = (dateStr) => {
    if (!dateStr) return 'Never used'
    const date = new Date(dateStr)
    return 'Last used: ' + date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  const maskedKey = project?.api_key
    ? project.api_key.slice(0, 8) + '\u2022'.repeat(32) + project.api_key.slice(-4)
    : ''

  if (loading) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <p className="text-gray-400 text-sm">Loading API key...</p>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">API Key</h2>
        <span className="text-sm text-gray-400">
          {formatLastUsed(project?.last_used_at)}
        </span>
      </div>

      <p className="text-sm text-gray-400 mb-3">
        Use this key to push scan results from your CI/CD pipeline via the API.
      </p>

      <div className="flex items-center gap-2">
        <input
          readOnly
          value={showKey ? (project?.api_key || '') : maskedKey}
          className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-300 font-mono"
          onClick={(e) => e.target.select()}
        />
        <button
          onClick={() => setShowKey((v) => !v)}
          className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded"
        >
          {showKey ? 'Hide' : 'Show'}
        </button>
        <button
          onClick={handleCopy}
          className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded"
        >
          Copy
        </button>
      </div>

      <div className="mt-4">
        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded disabled:opacity-50"
        >
          {regenerating ? 'Regenerating...' : 'Regenerate Key'}
        </button>
      </div>

      <p className="text-xs text-gray-500 mt-3">
        Include this key in the <span className="font-mono">Authorization: Api-Key &lt;key&gt;</span> header when pushing scans.
      </p>
    </div>
  )
}
