import { createContext, useContext, useState, useCallback } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => sessionStorage.getItem('token'))

  const login = async (username, password) => {
    const { data } = await api.post('/auth/login/', { username, password })
    sessionStorage.setItem('token', data.token)
    setToken(data.token)
    setUser(data.user)
  }

  const register = async (username, email, password) => {
    const { data } = await api.post('/auth/register/', { username, email, password })
    sessionStorage.setItem('token', data.token)
    setToken(data.token)
    setUser(data.user)
  }

  const logout = async () => {
    try { await api.post('/auth/logout/') } catch {}
    sessionStorage.removeItem('token')
    setToken(null)
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

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, updateUser, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
