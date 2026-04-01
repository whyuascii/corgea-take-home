import { useAuth } from '../context/AuthContext'
import useSessionTimeout from '../hooks/useSessionTimeout'

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export default function SessionTimeoutWarning() {
  const { logout } = useAuth()
  const { showWarning, resetTimer, timeRemaining } = useSessionTimeout(logout)

  if (!showWarning) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60">
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-sm shadow-2xl">
        {/* Warning icon */}
        <div className="flex items-center justify-center mb-4">
          <div className="w-12 h-12 rounded-full bg-yellow-500/20 flex items-center justify-center">
            <svg className="w-6 h-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
        </div>

        <h2 className="text-lg font-bold text-white text-center mb-2">
          Session Expiring
        </h2>
        <p className="text-sm text-gray-400 text-center mb-4">
          Your session will expire due to inactivity.
        </p>

        {/* Countdown */}
        <div className="text-center mb-6">
          <span className="text-3xl font-mono font-bold text-yellow-400">
            {formatTime(timeRemaining)}
          </span>
          <p className="text-xs text-gray-500 mt-1">remaining</p>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={logout}
            className="flex-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm font-medium transition-colors"
          >
            Logout Now
          </button>
          <button
            onClick={resetTimer}
            className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Stay Logged In
          </button>
        </div>
      </div>
    </div>
  )
}
