import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/auth/me/')
      .then(({ data }) => setUser(data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const login = async (username, password) => {
    const { data } = await api.post('/auth/login/', { username, password })
    setUser(data.user)
  }

  const register = async (username, email, password) => {
    const { data } = await api.post('/auth/register/', { username, email, password })
    setUser(data.user)
  }

  const logout = async () => {
    try { await api.post('/auth/logout/') } catch {}
    setUser(null)
  }

  const updateUser = useCallback((userData) => {
    setUser((prev) => ({ ...prev, ...userData }))
  }, [])

  const refreshUser = useCallback(async () => {
    try {
      const { data } = await api.get('/auth/me/')
      setUser(data)
      return data
    } catch (err) {
      console.error('Failed to refresh user:', err)
      throw err
    }
  }, [])

  if (loading) return null

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, register, logout, updateUser, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
