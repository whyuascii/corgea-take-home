import { useState, useEffect, useCallback } from 'react'
import api from '../api/client'

export default function APIKeyCard({ projectSlug }) {
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)
  const [newKey, setNewKey] = useState(null)
  const [regenerating, setRegenerating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState(null)

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
    if (newKey) {
      navigator.clipboard.writeText(newKey)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleRegenerate = async () => {
    if (!window.confirm('This will invalidate the existing key. Any CI/CD pipelines using the current key will stop working. Are you sure?')) {
      return
    }
    setRegenerating(true)
    setError(null)
    try {
      const { data } = await api.post(`/projects/${projectSlug}/rotate_api_key/`)
      setNewKey(data.api_key)
      setCopied(false)
      await fetchProject()
    } catch {
      setError('Failed to regenerate API key. Please try again.')
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

      {newKey ? (
        <div className="mb-3">
          <p className="text-sm text-yellow-400 mb-2">
            Copy your new API key now. It will not be shown again.
          </p>
          <div className="flex items-center gap-2">
            <input
              readOnly
              value={newKey}
              className="flex-1 bg-gray-800 border border-yellow-600 rounded px-3 py-2 text-sm text-gray-300 font-mono"
              onClick={(e) => e.target.select()}
            />
            <button
              onClick={handleCopy}
              className="px-3 py-2 bg-yellow-600 hover:bg-yellow-700 text-white text-sm rounded"
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-2 mb-3">
          <input
            readOnly
            value={project?.api_key_hint || '••••••••'}
            className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-300 font-mono"
          />
        </div>
      )}

      {error && (
        <p className="text-red-400 text-sm mt-2">{error}</p>
      )}

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
