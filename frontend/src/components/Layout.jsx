import { useParams, Outlet } from 'react-router-dom'
import TopNav from './TopNav'
import ProjectSubNav from './ProjectSubNav'
import { useProjectSafe } from '../context/ProjectContext'

export default function Layout() {
  const { slug } = useParams()
  const projectCtx = useProjectSafe()

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <TopNav />
      {slug && <ProjectSubNav project={projectCtx?.project ?? null} />}
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
