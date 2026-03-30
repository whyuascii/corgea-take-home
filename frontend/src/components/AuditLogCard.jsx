import { useState, useEffect } from 'react'
import api from '../api/client'

export default function AuditLogCard({ projectSlug }) {
  const [logs, setLogs] = useState([])
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    api.get(`/projects/${projectSlug}/findings/audit-log/`).then(r => {
      const data = r.data
      setLogs(Array.isArray(data) ? data : data.results || [])
    }).catch(() => {})
  }, [projectSlug])

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Audit Log</h2>
        <button onClick={() => setExpanded(!expanded)} className="text-sm text-gray-400 hover:text-white">
          {expanded ? 'Collapse' : 'Show All'}
        </button>
      </div>
      <div className="space-y-2">
        {(expanded ? logs : logs.slice(0, 10)).map(log => (
          <div key={log.id} className="flex items-center justify-between text-sm border-b border-gray-800 py-2 last:border-0">
            <div>
              <span className="text-gray-300">{log.action.replace(/_/g, ' ')}</span>
              {log.user && <span className="text-gray-500 ml-2">by {log.user}</span>}
            </div>
            <span className="text-gray-500 text-xs">{new Date(log.created_at).toLocaleString()}</span>
          </div>
        ))}
        {logs.length === 0 && <p className="text-gray-500 text-sm">No audit events yet</p>}
      </div>
    </div>
  )
}
