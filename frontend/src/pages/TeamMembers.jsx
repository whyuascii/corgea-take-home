import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'
import { getErrorMessage } from '../utils/errorMessages'

const ROLES = ['admin', 'member', 'viewer']

const roleBadgeColors = {
  owner: 'bg-indigo-500/20 text-indigo-400',
  admin: 'bg-yellow-500/20 text-yellow-400',
  member: 'bg-green-500/20 text-green-400',
  viewer: 'bg-gray-500/20 text-gray-400',
}

const roleDescriptions = [
  {
    role: 'Owner',
    description: 'Full control over the project. Can manage all settings, members, integrations, and delete the project.',
  },
  {
    role: 'Admin',
    description: 'Can manage findings, scans, integrations, and members. Cannot delete the project or transfer ownership.',
  },
  {
    role: 'Member',
    description: 'Can view and manage findings and scans. Cannot change project settings or manage members.',
  },
  {
    role: 'Viewer',
    description: 'Read-only access. Can view findings, scans, and project data but cannot make changes.',
  },
]

function RoleBadge({ role }) {
  const colorClass = roleBadgeColors[role] || 'bg-gray-700 text-gray-300'
  const label = role.charAt(0).toUpperCase() + role.slice(1)
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${colorClass}`}>
      {label}
    </span>
  )
}

export default function TeamMembers() {
  const { slug } = useParams()
  const { user } = useAuth()

  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Add member form
  const [newUsername, setNewUsername] = useState('')
  const [newRole, setNewRole] = useState('member')
  const [addLoading, setAddLoading] = useState(false)

  const isOwner = members.some(
    (m) => m.user?.username === user?.username && m.role === 'owner'
  )

  const fetchMembers = useCallback(async () => {
    try {
      const { data } = await api.get(`/projects/${slug}/members/`)
      setMembers(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load team members.'))
    } finally {
      setLoading(false)
    }
  }, [slug])

  useEffect(() => {
    fetchMembers()
  }, [fetchMembers])

  // Clear messages after a delay
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(''), 4000)
      return () => clearTimeout(timer)
    }
  }, [success])

  const handleAddMember = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!newUsername.trim()) {
      setError('Username is required.')
      return
    }

    setAddLoading(true)
    try {
      await api.post(`/projects/${slug}/members/`, {
        username: newUsername.trim(),
        role: newRole,
      })
      setNewUsername('')
      setNewRole('member')
      setSuccess(`Added ${newUsername.trim()} as ${newRole}.`)
      await fetchMembers()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to add member.'))
    } finally {
      setAddLoading(false)
    }
  }

  const handleChangeRole = async (membershipId, role) => {
    setError('')
    setSuccess('')
    try {
      await api.patch(`/projects/${slug}/members/${membershipId}/`, { role })
      setSuccess('Role updated.')
      await fetchMembers()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to update role.'))
    }
  }

  const handleRemoveMember = async (membershipId, username) => {
    setError('')
    setSuccess('')
    if (!window.confirm(`Remove ${username} from the project?`)) return

    try {
      await api.delete(`/projects/${slug}/members/${membershipId}/`)
      setSuccess(`Removed ${username}.`)
      await fetchMembers()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to remove member.'))
    }
  }

  const inputClasses =
    'px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500'

  if (loading) {
    return <div className="text-gray-400">Loading team members...</div>
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Team Members</h1>

      {/* Messages */}
      {error && (
        <div className="px-4 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}
      {success && (
        <div className="px-4 py-2 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400 text-sm">
          {success}
        </div>
      )}

      {/* Add member form (owner only) */}
      {isOwner && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Add Member</h2>
          <form onSubmit={handleAddMember} className="flex items-end gap-3">
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">Username</label>
              <input
                type="text"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                className={`${inputClasses} w-full`}
                placeholder="Enter username"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Role</label>
              <select
                value={newRole}
                onChange={(e) => setNewRole(e.target.value)}
                className={`${inputClasses} appearance-none pr-8`}
              >
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r.charAt(0).toUpperCase() + r.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              disabled={addLoading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 transition-colors whitespace-nowrap"
            >
              {addLoading ? 'Adding...' : 'Add'}
            </button>
          </form>
        </div>
      )}

      {/* Members list */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-800">
          <h2 className="text-lg font-semibold text-white">
            Members ({members.length})
          </h2>
        </div>

        <div className="divide-y divide-gray-800">
          {members.map((member) => {
            const memberUser = member.user || {}
            const memberIsOwner = member.role === 'owner'

            return (
              <div
                key={member.id}
                className="px-6 py-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-3 min-w-0">
                  {/* Avatar */}
                  <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-sm font-semibold text-gray-300 shrink-0">
                    {(memberUser.username || '?')[0].toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {memberUser.username || 'Unknown'}
                    </p>
                    {memberUser.email && (
                      <p className="text-xs text-gray-400 truncate">{memberUser.email}</p>
                    )}
                  </div>
                  <RoleBadge role={member.role} />
                </div>

                {/* Actions (owner only, cannot modify the owner row) */}
                {isOwner && !memberIsOwner && (
                  <div className="flex items-center gap-2 shrink-0 ml-4">
                    <select
                      value={member.role}
                      onChange={(e) => handleChangeRole(member.id, e.target.value)}
                      className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-sm text-white focus:outline-none focus:border-indigo-500"
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>
                          {r.charAt(0).toUpperCase() + r.slice(1)}
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={() => handleRemoveMember(member.id, memberUser.username)}
                      className="px-3 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded text-sm transition-colors"
                    >
                      Remove
                    </button>
                  </div>
                )}
              </div>
            )
          })}

          {members.length === 0 && (
            <div className="px-6 py-8 text-center text-gray-500 text-sm">
              No team members found.
            </div>
          )}
        </div>
      </div>

      {/* Role descriptions */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Role Permissions</h2>
        <div className="space-y-3">
          {roleDescriptions.map((rd) => (
            <div key={rd.role}>
              <div className="flex items-center gap-2 mb-1">
                <RoleBadge role={rd.role.toLowerCase()} />
              </div>
              <p className="text-sm text-gray-400 ml-1">{rd.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
