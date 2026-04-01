import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useParams, Outlet } from 'react-router-dom'
import api from '../api/client'

const ProjectContext = createContext(null)

export function ProjectProvider({ children }) {
  const { slug } = useParams()
  const [project, setProject] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchProject = useCallback(async (signal) => {
    if (!slug) {
      setProject(null)
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      const { data } = await api.get(`/projects/${slug}/`, { signal })
      setProject(data)
    } catch (err) {
      if (err.name === 'AbortError' || err.name === 'CanceledError') return
      console.error('Failed to fetch project:', err)
      setProject(null)
    } finally {
      setLoading(false)
    }
  }, [slug])

  useEffect(() => {
    const controller = new AbortController()
    fetchProject(controller.signal)
    return () => controller.abort()
  }, [fetchProject])

  const refetchProject = useCallback(() => fetchProject(), [fetchProject])

  const userRole = project?.user_role ?? null

  return (
    <ProjectContext.Provider value={{ project, userRole, loading, refetchProject }}>
      {children}
    </ProjectContext.Provider>
  )
}

export function useProject() {
  const ctx = useContext(ProjectContext)
  if (!ctx) throw new Error('useProject must be used within ProjectProvider')
  return ctx
}

/**
 * Safe version of useProject that returns null when used outside ProjectProvider.
 * Useful for components that optionally consume project context (e.g., Layout).
 */
export function useProjectSafe() {
  return useContext(ProjectContext)
}

/**
 * ProjectLayout wraps project routes with ProjectProvider and renders the Outlet.
 * Use this as the element for project route groups in the router.
 */
export function ProjectLayout() {
  return (
    <ProjectProvider>
      <Outlet />
    </ProjectProvider>
  )
}
