import { useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import api from '../api/client'
import { getErrorMessage } from '../utils/errorMessages'
import PasswordStrengthIndicator from '../components/PasswordStrengthIndicator'

export default function ResetPassword() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token') || ''

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!token) {
      setError('Invalid or missing reset token. Please request a new reset link.')
      return
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    if (!newPassword) {
      setError('Please enter a new password.')
      return
    }

    setLoading(true)
    try {
      await api.post('/auth/reset-password/', {
        token,
        password: newPassword,
      })
      // Redirect to login with a success state
      navigate('/login', { state: { message: 'Password reset successfully. Please sign in.' } })
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to reset password. The link may have expired.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="bg-gray-900 p-8 rounded-xl shadow-2xl w-full max-w-md border border-gray-800">
        <h1 className="text-2xl font-bold text-white mb-2">Set New Password</h1>
        <p className="text-sm text-gray-400 mb-6">
          Enter your new password below.
        </p>

        {!token && (
          <div className="space-y-4">
            <div className="px-4 py-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              Invalid or missing reset token. Please request a new reset link.
            </div>
            <p className="text-gray-400 text-sm">
              <Link to="/forgot-password" className="text-indigo-400 hover:underline">
                Request new reset link
              </Link>
            </p>
          </div>
        )}

        {token && (
          <>
            {error && <p className="text-red-400 mb-4 text-sm">{error}</p>}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">New Password</label>
                <input
                  type="password"
                  placeholder="New password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                />
                <PasswordStrengthIndicator password={newPassword} />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Confirm Password</label>
                <input
                  type="password"
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                />
                {confirmPassword && newPassword !== confirmPassword && (
                  <p className="text-red-400 text-xs mt-1">Passwords do not match.</p>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium disabled:opacity-50 transition-colors"
              >
                {loading ? 'Resetting...' : 'Reset Password'}
              </button>
            </form>
            <p className="text-gray-400 text-sm mt-4">
              <Link to="/login" className="text-indigo-400 hover:underline">
                Back to Sign In
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  )
}
