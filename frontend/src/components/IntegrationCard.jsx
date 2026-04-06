import { useState, useEffect } from 'react'
import api from '../api/client'

const INTERNAL_STATUSES = ['new', 'open', 'resolved', 'reopened', 'ignored']

function Field({ label, value, onChange, type = 'text', placeholder }) {
  return (
    <div>
      <label className="block text-sm text-gray-400 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500"
      />
    </div>
  )
}

export default function IntegrationCard({ provider, config, projectSlug, onRefresh }) {
  const isJira = provider === 'jira'
  const label = isJira ? 'Jira' : 'Linear'

  const [form, setForm] = useState({
    is_enabled: false,
    jira_instance_url: '',
    jira_project_key: '',
    jira_api_token: '',
    jira_user_email: '',
    linear_api_key: '',
    linear_team_id: '',
  })
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [mappings, setMappings] = useState([])
  const [newMapping, setNewMapping] = useState({ external_status: '', internal_status: 'resolved' })
  const [error, setError] = useState(null)

  useEffect(() => {
    if (config) {
      setForm({
        is_enabled: config.is_enabled,
        jira_instance_url: config.jira_instance_url || '',
        jira_project_key: config.jira_project_key || '',
        jira_api_token: '',
        jira_user_email: config.jira_user_email || '',
        linear_api_key: '',
        linear_team_id: config.linear_team_id || '',
      })
      setMappings(config.status_mappings || [])
    }
  }, [config])

  const handleChange = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setForm((f) => ({ ...f, [field]: value }))
  }

  const handleSave = async () => {
    setSaving(true)
    setTestResult(null)
    setError(null)
    try {
      const payload = { provider, ...form }
      // Don't send empty token fields on update
      if (config && !payload.jira_api_token) delete payload.jira_api_token
      if (config && !payload.linear_api_key) delete payload.linear_api_key

      if (config) {
        await api.patch(`/projects/${projectSlug}/integrations/${config.id}/`, payload)
      } else {
        await api.post(`/projects/${projectSlug}/integrations/`, payload)
      }
      onRefresh()
    } catch {
      setError('Failed to save integration. Please check your settings and try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    if (!config) return
    setTesting(true)
    setTestResult(null)
    try {
      const { data } = await api.post(`/projects/${projectSlug}/integrations/${config.id}/test/`)
      setTestResult(data)
    } catch (err) {
      setTestResult({ ok: false, error: err.message })
    } finally {
      setTesting(false)
    }
  }

  const addMapping = async () => {
    if (!config || !newMapping.external_status) return
    try {
      await api.post(`/projects/${projectSlug}/integrations/${config.id}/mappings/`, newMapping)
      setNewMapping({ external_status: '', internal_status: 'resolved' })
      onRefresh()
    } catch {
      setError('Failed to add mapping. Please try again.')
    }
  }

  const deleteMapping = async (mappingId) => {
    if (!config) return
    try {
      await api.delete(`/projects/${projectSlug}/integrations/${config.id}/mappings/${mappingId}/`)
      onRefresh()
    } catch {
      setError('Failed to delete mapping. Please try again.')
    }
  }

  const webhookUrl = config
    ? `${window.location.origin}/api/webhooks/${provider}/${config.webhook_secret}/`
    : ''

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">{label} Integration</h2>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={form.is_enabled}
            onChange={handleChange('is_enabled')}
            className="w-4 h-4 rounded bg-gray-800 border-gray-600"
          />
          <span className="text-sm text-gray-400">Enabled</span>
        </label>
      </div>

      <div className="space-y-3">
        {isJira ? (
          <>
            <Field label="Instance URL" value={form.jira_instance_url} onChange={handleChange('jira_instance_url')} placeholder="https://yourcompany.atlassian.net" />
            <Field label="Project Key" value={form.jira_project_key} onChange={handleChange('jira_project_key')} placeholder="PROJ" />
            <Field label="User Email" value={form.jira_user_email} onChange={handleChange('jira_user_email')} placeholder="user@company.com" />
            <Field label="API Token" value={form.jira_api_token} onChange={handleChange('jira_api_token')} type="password" placeholder={config?.jira_api_token_set ? '(token set - leave blank to keep)' : 'Enter API token'} />
          </>
        ) : (
          <>
            <Field label="API Key" value={form.linear_api_key} onChange={handleChange('linear_api_key')} type="password" placeholder={config?.linear_api_key_set ? '(key set - leave blank to keep)' : 'Enter API key'} />
            <Field label="Team ID" value={form.linear_team_id} onChange={handleChange('linear_team_id')} placeholder="Team ID from Linear settings" />
          </>
        )}
      </div>

      <div className="flex gap-3 mt-4">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save'}
        </button>
        {config && (
          <button
            onClick={handleTest}
            disabled={testing}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded disabled:opacity-50"
          >
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
        )}
      </div>

      {error && (
        <p className="mt-3 text-red-400 text-sm">{error}</p>
      )}

      {testResult && (
        <div className={`mt-3 p-3 rounded text-sm ${testResult.ok ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
          {testResult.ok
            ? `Connected successfully${testResult.project_name ? ` (${testResult.project_name})` : ''}${testResult.team_name ? ` (${testResult.team_name})` : ''}`
            : `Connection failed: ${testResult.error}`}
        </div>
      )}

      {config && (
        <>
          <div className="mt-6 pt-4 border-t border-gray-800">
            <h3 className="text-sm font-medium text-gray-300 mb-2">Webhook URL</h3>
            <div className="flex items-center gap-2">
              <input
                readOnly
                value={webhookUrl}
                className="flex-1 bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-gray-300 font-mono"
                onClick={(e) => e.target.select()}
              />
              <button
                onClick={() => navigator.clipboard.writeText(webhookUrl)}
                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded"
              >
                Copy
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Configure this URL in your {label} webhook settings to receive status updates.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-800">
            <h3 className="text-sm font-medium text-gray-300 mb-3">Status Mappings</h3>
            <p className="text-xs text-gray-500 mb-3">
              Map {label} statuses to VulnTracker finding statuses for automatic sync.
            </p>

            {mappings.length > 0 && (
              <table className="w-full text-sm mb-3">
                <thead>
                  <tr className="text-gray-400 text-left">
                    <th className="pb-2">{label} Status</th>
                    <th className="pb-2">VulnTracker Status</th>
                    <th className="pb-2 w-16"></th>
                  </tr>
                </thead>
                <tbody>
                  {mappings.map((m) => (
                    <tr key={m.id} className="border-t border-gray-800">
                      <td className="py-2 text-gray-300">{m.external_status}</td>
                      <td className="py-2 text-gray-300">{m.internal_status}</td>
                      <td className="py-2">
                        <button
                          onClick={() => deleteMapping(m.id)}
                          className="text-red-400 hover:text-red-300 text-xs"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            <div className="flex gap-2 items-end">
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">{label} Status</label>
                <input
                  value={newMapping.external_status}
                  onChange={(e) => setNewMapping((m) => ({ ...m, external_status: e.target.value }))}
                  placeholder="e.g. Done"
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
                />
              </div>
              <div className="flex-1">
                <label className="block text-xs text-gray-500 mb-1">VulnTracker Status</label>
                <select
                  value={newMapping.internal_status}
                  onChange={(e) => setNewMapping((m) => ({ ...m, internal_status: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm text-white"
                >
                  {INTERNAL_STATUSES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={addMapping}
                disabled={!newMapping.external_status}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded disabled:opacity-50"
              >
                Add
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
