import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import PasswordStrengthIndicator from '../components/PasswordStrengthIndicator'

export default function Register() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await register(username, email, password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.username?.[0] || err.response?.data?.password?.[0] || 'Registration failed')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="bg-gray-900 p-8 rounded-xl shadow-2xl w-full max-w-md border border-gray-800">
        <h1 className="text-2xl font-bold text-white mb-6">Create Account</h1>
        {error && <p className="text-red-400 mb-4 text-sm">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500" />
          <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500" />
          <div>
            <input type="password" placeholder="Password (10+ chars)" value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-indigo-500" />
            <PasswordStrengthIndicator password={password} />
          </div>
          <button type="submit" className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium">Register</button>
        </form>
        <p className="text-gray-400 text-sm mt-4">
          Have an account? <Link to="/login" className="text-indigo-400 hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
