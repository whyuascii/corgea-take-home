import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import api from '../api/client'
import APIKeyCard from '../components/APIKeyCard'
import IntegrationCard from '../components/IntegrationCard'
import AuditLogCard from '../components/AuditLogCard'

export default function ProjectSettings() {
  const { slug } = useParams()
  const [integrations, setIntegrations] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchIntegrations = useCallback(async () => {
    try {
      const { data } = await api.get(`/projects/${slug}/integrations/`)
      setIntegrations(data)
    } catch (err) {
      console.error('Failed to load integrations', err)
    } finally {
      setLoading(false)
    }
  }, [slug])

  useEffect(() => { fetchIntegrations() }, [fetchIntegrations])

  const jiraConfig = integrations.find((i) => i.provider === 'jira') || null
  const linearConfig = integrations.find((i) => i.provider === 'linear') || null

  if (loading) {
    return <div className="text-gray-400">Loading settings...</div>
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold text-white mb-6">Project Settings</h1>
      <div className="space-y-6">
        <APIKeyCard projectSlug={slug} />
        <IntegrationCard
          provider="jira"
          config={jiraConfig}
          projectSlug={slug}
          onRefresh={fetchIntegrations}
        />
        <IntegrationCard
          provider="linear"
          config={linearConfig}
          projectSlug={slug}
          onRefresh={fetchIntegrations}
        />
        <AuditLogCard projectSlug={slug} />
      </div>
    </div>
  )
}
