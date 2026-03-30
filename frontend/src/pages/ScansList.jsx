import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'
import { extractResults, getTotalPages } from '../api/helpers'
import Pagination from '../components/Pagination'

const PAGE_SIZE = 25

export default function ScansList() {
  const { slug } = useParams()
  const [scans, setScans] = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null) // { type: 'success'|'error', message }
  const [page, setPage] = useState(1)
  const fileRef = useRef()

  useEffect(() => { fetchScans() }, [slug, page])

  const fetchScans = async () => {
    setLoading(true)
    try {
      const { data } = await api.get(`/projects/${slug}/scans/?page=${page}`)
      const parsed = extractResults(data)
      setScans(parsed.results)
      setTotalCount(parsed.count)
    } catch (err) {
      console.error('Failed to fetch scans:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setUploadResult(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const { data } = await api.post(`/projects/${slug}/scans/upload/`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      const summary = data.summary || {}
      let message = `Scan uploaded: ${summary.new || 0} new, ${summary.reopened || 0} reopened, ${summary.resolved || 0} resolved`
      if (summary.skipped) {
        message += ` (${summary.skipped} malformed results skipped)`
      }
      setUploadResult({ type: 'success', message })
      setTimeout(() => setUploadResult(null), 6000)
      fetchScans()
    } catch (err) {
      const errData = err.response?.data
      let message = 'Upload failed'
      if (errData?.file) {
        message = Array.isArray(errData.file) ? errData.file.join(' ') : errData.file
      } else if (errData?.detail) {
        message = errData.detail
      } else if (err.message) {
        message = err.message
      }
      setUploadResult({ type: 'error', message })
    }
    setUploading(false)
    fileRef.current.value = ''
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h1 className="text-2xl font-bold">Scans</h1>
        <div className="flex items-center gap-3">
          {uploadResult && (
            <div className={`flex items-center gap-2 text-sm font-medium ${
              uploadResult.type === 'success' ? 'text-green-400' : 'text-red-400'
            }`}>
              <span>{uploadResult.message}</span>
              <button onClick={() => setUploadResult(null)} className="text-gray-500 hover:text-gray-300 ml-1">&times;</button>
            </div>
          )}
          <label className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium cursor-pointer transition-colors ${
            uploading
              ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700 text-white'
          }`}>
            {uploading && (
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-400 border-t-white"></div>
            )}
            {uploading ? 'Uploading...' : 'Upload Report'}
            <input type="file" accept=".json" ref={fileRef} onChange={handleUpload} className="hidden" disabled={uploading} />
          </label>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-800/50">
              <tr>
                <th className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Date</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Source</th>
                <th className="text-left px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Branch</th>
                <th className="text-right px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Total</th>
                <th className="text-right px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">New</th>
                <th className="text-right px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Reopened</th>
                <th className="text-right px-4 py-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Resolved</th>
              </tr>
            </thead>
            <tbody>
              {!loading && scans.map((s) => (
                <tr key={s.id} className="border-t border-gray-800 hover:bg-gray-800/30">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <Link to={`/projects/${slug}/scans/${s.id}`} className="text-indigo-400 hover:underline">
                      {new Date(s.scanned_at).toLocaleString()}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-400">{s.source}</td>
                  <td className="px-4 py-3 text-gray-400 font-mono text-xs max-w-[200px] truncate" title={s.branch || ''}>
                    {s.branch || '\u2014'}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums">{s.total_findings_count}</td>
                  <td className="px-4 py-3 text-right text-blue-400 tabular-nums">{s.new_count}</td>
                  <td className="px-4 py-3 text-right text-orange-400 tabular-nums">{s.reopened_count}</td>
                  <td className="px-4 py-3 text-right text-green-400 tabular-nums">{s.resolved_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-6 w-6 border-2 border-gray-600 border-t-indigo-500"></div>
              <span className="ml-3 text-gray-400 text-sm">Loading scans...</span>
            </div>
          )}
          {!loading && scans.length === 0 && <p className="text-gray-500 text-center py-8">No scans yet</p>}
        </div>
      </div>

      <Pagination page={page} totalPages={getTotalPages(totalCount, PAGE_SIZE)} onPageChange={setPage} />
    </div>
  )
}
