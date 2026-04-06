import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'
import { extractResults, getTotalPages } from '../api/helpers'
import StatusBadge from '../components/StatusBadge'
import Pagination from '../components/Pagination'

const PAGE_SIZE = 25

export default function ScanDetail() {
  const { slug, scanId } = useParams()
  const [scan, setScan] = useState(null)
  const [findings, setFindings] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
  const [error, setError] = useState(null)

  useEffect(() => {
    const controller = new AbortController()
    api.get(`/projects/${slug}/scans/${scanId}/`, { signal: controller.signal })
      .then((r) => setScan(r.data))
      .catch((err) => { if (!controller.signal.aborted) setError('Failed to load scan details.') })
    return () => controller.abort()
  }, [slug, scanId])

  useEffect(() => {
    const controller = new AbortController()
    api.get(`/projects/${slug}/findings/?scan=${scanId}&page=${page}`, { signal: controller.signal })
      .then((r) => {
        const parsed = extractResults(r.data)
        setFindings(parsed.results)
        setTotalCount(parsed.count)
      })
      .catch((err) => { if (!controller.signal.aborted) setError('Failed to load findings.') })
    return () => controller.abort()
  }, [slug, scanId, page])

  if (error) return <p className="text-red-400">{error}</p>
  if (!scan) return <p className="text-gray-500">Loading...</p>

  return (
    <div>
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Scan Detail</h1>
          <p className="text-gray-300 text-sm mt-1">
            {new Date(scan.scanned_at).toLocaleString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {scan.source && (
            <span className="px-2 py-1 bg-gray-800 text-gray-400 rounded text-xs">
              {scan.source}
            </span>
          )}
        </div>
      </div>

      {/* Scan metadata row */}
      <div className="flex flex-wrap gap-3 mb-6">
        {scan.commit_sha && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-900 border border-gray-800 rounded-lg text-xs">
            <span className="text-gray-500">Commit</span>
            <span className="text-white font-mono bg-gray-800 px-1.5 py-0.5 rounded">{scan.commit_sha.substring(0, 8)}</span>
          </span>
        )}
        {scan.branch && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-900 border border-gray-800 rounded-lg text-xs">
            <span className="text-gray-500">Branch</span>
            <span className="text-white font-mono">{scan.branch}</span>
          </span>
        )}
        {scan.ci_provider && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-900 border border-gray-800 rounded-lg text-xs">
            <span className="text-gray-500">CI</span>
            <span className="text-white">{scan.ci_provider}</span>
          </span>
        )}
        {scan.source && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-900 border border-gray-800 rounded-lg text-xs">
            <span className="text-gray-500">Source</span>
            <span className="text-white">{scan.source}</span>
          </span>
        )}
        {scan.uploaded_by && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-gray-900 border border-gray-800 rounded-lg text-xs">
            <span className="text-gray-500">Uploaded by</span>
            <span className="text-white">{scan.uploaded_by}</span>
          </span>
        )}
      </div>

      {/* Stats cards with colored left border accents */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-900 border border-gray-800 border-l-4 border-l-gray-400 rounded-xl p-4">
          <p className="text-gray-400 text-xs">Total</p>
          <p className="text-xl font-bold">{scan.total_findings_count}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 border-l-4 border-l-blue-500 rounded-xl p-4">
          <p className="text-gray-400 text-xs">New</p>
          <p className="text-xl font-bold text-blue-400">{scan.new_count}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 border-l-4 border-l-orange-500 rounded-xl p-4">
          <p className="text-gray-400 text-xs">Reopened</p>
          <p className="text-xl font-bold text-orange-400">{scan.reopened_count}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 border-l-4 border-l-green-500 rounded-xl p-4">
          <p className="text-gray-400 text-xs">Resolved</p>
          <p className="text-xl font-bold text-green-400">{scan.resolved_count}</p>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Rule</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">File</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Line</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Severity</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {findings.map((f) => (
              <tr key={f.id} className="border-t border-gray-800 hover:bg-gray-800/30">
                <td className="px-4 py-3 font-mono text-xs">
                  <Link to={`/projects/${slug}/findings/${f.id}`} className="text-indigo-400 hover:underline">{f.rule_id_display}</Link>
                </td>
                <td className="px-4 py-3 text-gray-300 font-mono text-xs">{f.file_path}</td>
                <td className="px-4 py-3 text-gray-400">{f.line_start}-{f.line_end}</td>
                <td className="px-4 py-3"><StatusBadge value={f.severity} /></td>
                <td className="px-4 py-3"><StatusBadge value={f.status} /></td>
              </tr>
            ))}
            {findings.length === 0 && (
              <tr>
                <td colSpan="5" className="px-4 py-6 text-center text-gray-500">No findings for this scan</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <Pagination page={page} totalPages={getTotalPages(totalCount, PAGE_SIZE)} onPageChange={setPage} />
    </div>
  )
}
