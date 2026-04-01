import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/client'
import { getErrorMessage } from '../utils/errorMessages'
import PasswordStrengthIndicator from '../components/PasswordStrengthIndicator'

export default function AccountSettings() {
  const { user, updateUser } = useAuth()

  // ── Profile state ──
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [profilePassword, setProfilePassword] = useState('')
  const [profileSuccess, setProfileSuccess] = useState('')
  const [profileError, setProfileError] = useState('')
  const [profileLoading, setProfileLoading] = useState(false)

  // ── Password state ──
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordSuccess, setPasswordSuccess] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [passwordLoading, setPasswordLoading] = useState(false)

  // Populate form from user context
  useEffect(() => {
    if (user) {
      setFirstName(user.first_name || '')
      setLastName(user.last_name || '')
      setEmail(user.email || '')
    }
  }, [user])

  // ── Profile submit ──
  const handleProfileSubmit = async (e) => {
    e.preventDefault()
    setProfileSuccess('')
    setProfileError('')

    if (!profilePassword) {
      setProfileError('Current password is required to update your profile.')
      return
    }

    setProfileLoading(true)
    try {
      const { data } = await api.patch('/auth/me/', {
        first_name: firstName,
        last_name: lastName,
        email,
        current_password: profilePassword,
      })
      updateUser(data)
      setProfilePassword('')
      setProfileSuccess('Profile updated successfully.')
    } catch (err) {
      setProfileError(getErrorMessage(err, 'Failed to update profile.'))
    } finally {
      setProfileLoading(false)
    }
  }

  // ── Password submit ──
  const handlePasswordSubmit = async (e) => {
    e.preventDefault()
    setPasswordSuccess('')
    setPasswordError('')

    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match.')
      return
    }

    if (!currentPassword) {
      setPasswordError('Current password is required.')
      return
    }

    setPasswordLoading(true)
    try {
      await api.post('/auth/change-password/', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setPasswordSuccess('Password changed successfully.')
    } catch (err) {
      setPasswordError(getErrorMessage(err, 'Failed to change password.'))
    } finally {
      setPasswordLoading(false)
    }
  }

  const inputClasses =
    'w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500'

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Account Settings</h1>

      {/* ── Profile Card ── */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Profile</h2>

        {profileSuccess && (
          <div className="mb-4 px-4 py-2 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400 text-sm">
            {profileSuccess}
          </div>
        )}
        {profileError && (
          <div className="mb-4 px-4 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            {profileError}
          </div>
        )}

        <form onSubmit={handleProfileSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">First Name</label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className={inputClasses}
                placeholder="First name"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Last Name</label>
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className={inputClasses}
                placeholder="Last name"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClasses}
              placeholder="Email address"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">
              Current Password <span className="text-red-400">*</span>
            </label>
            <input
              type="password"
              value={profilePassword}
              onChange={(e) => setProfilePassword(e.target.value)}
              className={inputClasses}
              placeholder="Required to save changes"
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={profileLoading}
              className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium text-sm disabled:opacity-50 transition-colors"
            >
              {profileLoading ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        </form>
      </div>

      {/* ── Security Card (Change Password) ── */}
      <div id="password" className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Change Password</h2>

        {passwordSuccess && (
          <div className="mb-4 px-4 py-2 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400 text-sm">
            {passwordSuccess}
          </div>
        )}
        {passwordError && (
          <div className="mb-4 px-4 py-2 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            {passwordError}
          </div>
        )}

        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Current Password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className={inputClasses}
              placeholder="Current password"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className={inputClasses}
              placeholder="New password"
            />
            <PasswordStrengthIndicator password={newPassword} />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={inputClasses}
              placeholder="Confirm new password"
            />
            {confirmPassword && newPassword !== confirmPassword && (
              <p className="text-red-400 text-xs mt-1">Passwords do not match.</p>
            )}
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={passwordLoading}
              className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium text-sm disabled:opacity-50 transition-colors"
            >
              {passwordLoading ? 'Changing...' : 'Change Password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
