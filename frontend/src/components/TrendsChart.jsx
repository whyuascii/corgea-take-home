import { useEffect, useState } from 'react'
import api from '../api/client'

export default function TrendsChart({ slug }) {
  const [trends, setTrends] = useState([])

  useEffect(() => {
    api.get(`/projects/${slug}/findings/trends/?days=30`).then(r => setTrends(r.data))
  }, [slug])

  if (!trends.length) return null

  const maxVal = Math.max(...trends.map(t => Math.max(t.new, t.resolved)), 1)

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
      <h2 className="font-semibold mb-3">Finding Trends (30 days)</h2>
      <div className="flex items-end gap-1 h-36">
        {trends.map((t) => (
          <div
            key={t.date}
            className="flex-1 flex flex-col items-center justify-end h-full group relative"
          >
            <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-800 text-gray-200 text-xs rounded px-2 py-1 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 border border-gray-700">
              {t.date}: +{t.new} new, -{t.resolved} resolved
            </div>
            <div className="w-full flex flex-col items-center gap-0.5 h-full justify-end">
              <div
                className="w-full bg-blue-500/70 rounded-t transition-all group-hover:bg-blue-400/80"
                style={{
                  height: `${(t.new / maxVal) * 100}%`,
                  minHeight: t.new ? '3px' : '0',
                  minWidth: '4px',
                }}
              />
              <div
                className="w-full bg-green-500/70 rounded-b transition-all group-hover:bg-green-400/80"
                style={{
                  height: `${(t.resolved / maxVal) * 100}%`,
                  minHeight: t.resolved ? '3px' : '0',
                  minWidth: '4px',
                }}
              />
            </div>
          </div>
        ))}
      </div>
      <div className="flex justify-between text-xs text-gray-500 mt-2">
        <span>{trends[0]?.date}</span>
        <div className="flex gap-4">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 bg-blue-500/70 rounded inline-block" /> New
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 bg-green-500/70 rounded inline-block" /> Resolved
          </span>
        </div>
        <span>{trends[trends.length - 1]?.date}</span>
      </div>
    </div>
  )
}
