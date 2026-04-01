import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { getErrorMessage } from '../utils/errorMessages'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!email.trim()) {
      setError('Please enter your email address.')
      return
    }

    setLoading(true)
    try {
      await api.post('/auth/forgot-password/', { email: email.trim() })
      setSubmitted(true)
    } catch (err) {
      // Even on error, show the generic message to avoid email enumeration
      // Only show a real error if it's a network/server issue
      if (!err.response || err.response.status >= 500) {
        setError(getErrorMessage(err, 'Something went wrong. Please try again later.'))
      } else {
        setSubmitted(true)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="bg-gray-900 p-8 rounded-xl shadow-2xl w-full max-w-md border border-gray-800">
        <h1 className="text-2xl font-bold text-white mb-2">Reset Password</h1>
        <p className="text-sm text-gray-400 mb-6">
          Enter your email address and we will send you a link to reset your password.
        </p>

        {submitted ? (
          <div className="space-y-4">
            <div className="px-4 py-3 bg-green-500/10 border border-green-500/30 rounded-lg text-green-400 text-sm">
              If an account with that email exists, a reset link has been sent.
            </div>
            <p className="text-gray-400 text-sm">
              <Link to="/login" className="text-indigo-400 hover:underline">
                Back to Sign In
              </Link>
            </p>
          </div>
        ) : (
          <>
            {error && <p className="text-red-400 mb-4 text-sm">{error}</p>}
            <form onSubmit={handleSubmit} className="space-y-4">
              <input
                type="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium disabled:opacity-50 transition-colors"
              >
                {loading ? 'Sending...' : 'Send Reset Link'}
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
