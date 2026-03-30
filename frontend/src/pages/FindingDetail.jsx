import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client'
import StatusBadge from '../components/StatusBadge'
import FalsePositiveModal from '../components/FalsePositiveModal'
import SecurityDetails from '../components/SecurityDetails'
import FindingComments from '../components/FindingComments'
import FindingHistory from '../components/FindingHistory'
import { useAuth } from '../context/AuthContext'

export default function FindingDetail() {
  const { slug, findingId } = useParams()
  const { user } = useAuth()
  const [finding, setFinding] = useState(null)
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({})
  const [fpModalOpen, setFpModalOpen] = useState(false)
  const [commentText, setCommentText] = useState('')
  const [commentLoading, setCommentLoading] = useState(false)
  const [historyExpanded, setHistoryExpanded] = useState(false)

  useEffect(() => { fetchFinding() }, [slug, findingId])

  const fetchFinding = async () => {
    const { data } = await api.get(`/projects/${slug}/findings/${findingId}/`)
    setFinding(data)
    setForm({
      jira_ticket_url: data.jira_ticket_url || '',
      linear_ticket_url: data.linear_ticket_url || '',
      pr_url: data.pr_url || '',
    })
  }

  const handleSave = async () => {
    await api.patch(`/projects/${slug}/findings/${findingId}/`, form)
    setEditing(false)
    fetchFinding()
  }

  const handleFalsePositive = async (payload) => {
    await api.post(`/projects/${slug}/findings/${findingId}/false-positive/`, payload)
    fetchFinding()
  }

  const handleAddComment = async () => {
    if (!commentText.trim()) return
    setCommentLoading(true)
    try {
      await api.post(`/projects/${slug}/findings/${findingId}/comments/`, { text: commentText })
      setCommentText('')
      fetchFinding()
    } finally {
      setCommentLoading(false)
    }
  }

  const handleDeleteComment = async (commentId) => {
    await api.delete(`/projects/${slug}/findings/${findingId}/comments/${commentId}/`)
    fetchFinding()
  }

  if (!finding) return <p className="text-gray-500">Loading...</p>

  const severity = finding.effective_severity || finding.severity
  const ruleMessage = finding.rule_message || finding.message || finding.metadata?.message || null
  const historyItems = finding.history || []

  return (
    <div>
      {/* ========== Full-width header banner ========== */}
      <div className={`border-t-4 ${
        severity === 'ERROR' ? 'border-t-red-500' :
        severity === 'WARNING' ? 'border-t-yellow-500' : 'border-t-blue-500'
      } bg-gray-900 border-b border-gray-800 -mx-6 -mt-6 px-6 py-5 mb-6`}>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <h1 className="text-xl font-bold font-mono text-white">{finding.rule_id_display}</h1>
            <p className="text-gray-500 text-sm mt-1 font-mono truncate">
              {finding.file_path}
              <span className="text-gray-600">:</span>
              <span className="text-gray-400">{finding.line_start}-{finding.line_end}</span>
            </p>
            {ruleMessage && (
              <p className="text-gray-300 text-sm mt-3 leading-relaxed max-w-3xl">{ruleMessage}</p>
            )}
          </div>
          <div className="flex items-center gap-2 flex-shrink-0 pt-1">
            <StatusBadge value={severity} />
            <StatusBadge value={finding.status} />
            {finding.is_false_positive && <StatusBadge value="false_positive" />}
            <button
              onClick={() => setFpModalOpen(true)}
              className={
                finding.is_false_positive
                  ? 'bg-purple-600 text-white px-4 py-1.5 rounded-lg text-xs font-medium hover:bg-purple-700 transition-colors ml-1'
                  : 'border border-gray-600 text-gray-300 hover:border-purple-500 hover:text-purple-400 px-4 py-1.5 rounded-lg text-xs font-medium transition-colors ml-1'
              }
            >
              <span className="inline-flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 3v1.5M3 21v-6m0 0 2.77-.693a9 9 0 0 1 6.208.682l.108.054a9 9 0 0 0 6.086.71l3.114-.732a48.524 48.524 0 0 1-.005-10.499l-3.11.732a9 9 0 0 1-6.085-.711l-.108-.054a9 9 0 0 0-6.208-.682L3 4.5M3 15V4.5" />
                </svg>
                {finding.is_false_positive ? 'Unmark FP' : 'Mark as FP'}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* ========== Two-column layout ========== */}
      <div className="flex gap-6">

        {/* ---- Left column (2/3 width) ---- */}
        <div className="flex-1 min-w-0">

          {/* FP Reason banner */}
          {finding.is_false_positive && finding.false_positive_reason && (
            <div className="bg-purple-500/10 border border-purple-500/20 rounded-xl p-4 mb-6">
              <p className="text-sm text-purple-300">
                <span className="font-medium">FP Reason:</span> {finding.false_positive_reason}
              </p>
            </div>
          )}

          {/* Code snippet */}
          {finding.code_snippet && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-6">
              <h2 className="text-sm font-medium text-gray-400 mb-2">Code</h2>
              <pre className="text-sm text-gray-300 overflow-x-auto font-mono leading-relaxed">{finding.code_snippet}</pre>
            </div>
          )}

          {/* Security Details */}
          <SecurityDetails metadata={finding.metadata} />

          {/* Tracking */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-medium text-gray-400">Tracking</h2>
              <button onClick={() => editing ? handleSave() : setEditing(true)}
                className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 rounded text-xs">
                {editing ? 'Save' : 'Edit'}
              </button>
            </div>
            {editing ? (
              <div className="space-y-2">
                <input placeholder="Jira ticket URL" value={form.jira_ticket_url}
                  onChange={(e) => setForm({ ...form, jira_ticket_url: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
                <input placeholder="Linear ticket URL" value={form.linear_ticket_url}
                  onChange={(e) => setForm({ ...form, linear_ticket_url: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
                <input placeholder="PR URL" value={form.pr_url}
                  onChange={(e) => setForm({ ...form, pr_url: e.target.value })}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white" />
              </div>
            ) : (
              <div className="space-y-1 text-sm">
                <p><span className="text-gray-500">Jira:</span> {finding.jira_ticket_url ? <a href={finding.jira_ticket_url} className="text-indigo-400 hover:underline" target="_blank" rel="noreferrer">{finding.jira_ticket_url}</a> : <span className="text-gray-600">&mdash;</span>}</p>
                <p><span className="text-gray-500">Linear:</span> {finding.linear_ticket_url ? <a href={finding.linear_ticket_url} className="text-indigo-400 hover:underline" target="_blank" rel="noreferrer">{finding.linear_ticket_url}</a> : <span className="text-gray-600">&mdash;</span>}</p>
                <p><span className="text-gray-500">PR:</span> {finding.pr_url ? <a href={finding.pr_url} className="text-indigo-400 hover:underline" target="_blank" rel="noreferrer">{finding.pr_url}</a> : <span className="text-gray-600">&mdash;</span>}</p>
              </div>
            )}
          </div>
        </div>

        {/* ---- Right column (sidebar, sticky) ---- */}
        <div className="w-80 flex-shrink-0">
          <div className="sticky top-6 space-y-6">

            {/* Quick Info card */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Details</h3>
              <div className="space-y-2.5 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">Severity</span>
                  <StatusBadge value={severity} />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">Status</span>
                  <StatusBadge value={finding.status} />
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">First Seen</span>
                  <span className="text-gray-300 text-xs">{finding.created_at ? new Date(finding.created_at).toLocaleDateString() : '\u2014'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">Last Updated</span>
                  <span className="text-gray-300 text-xs">{finding.updated_at ? new Date(finding.updated_at).toLocaleDateString() : '\u2014'}</span>
                </div>
                {finding.is_false_positive && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500">FP Status</span>
                    <span className="text-purple-400 text-xs font-medium">Marked as FP</span>
                  </div>
                )}
              </div>
            </div>

            {/* History timeline (compact) */}
            <FindingHistory
              historyItems={historyItems}
              historyExpanded={historyExpanded}
              onToggleExpanded={() => setHistoryExpanded(!historyExpanded)}
            />

            {/* Comments */}
            <FindingComments
              comments={finding.comments}
              commentText={commentText}
              onCommentTextChange={setCommentText}
              onAddComment={handleAddComment}
              onDeleteComment={handleDeleteComment}
              commentLoading={commentLoading}
              currentUsername={user?.username}
            />

          </div>
        </div>

      </div>

      {/* FP Modal */}
      <FalsePositiveModal
        isOpen={fpModalOpen}
        onClose={() => setFpModalOpen(false)}
        onConfirm={handleFalsePositive}
        isCurrentlyFP={finding.is_false_positive}
      />
    </div>
  )
}
