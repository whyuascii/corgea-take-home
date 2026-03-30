import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './components/Toast'
import ErrorBoundary from './components/ErrorBoundary'
import Login from './pages/Login'
import Register from './pages/Register'
import ProjectsList from './pages/ProjectsList'
import ProjectDashboard from './pages/ProjectDashboard'
import ScansList from './pages/ScansList'
import ScanDetail from './pages/ScanDetail'
import RulesList from './pages/RulesList'
import FindingsList from './pages/FindingsList'
import FindingDetail from './pages/FindingDetail'
import ProjectSettings from './pages/ProjectSettings'
import CrossProjectOverview from './pages/CrossProjectOverview'
import HowTo from './pages/HowTo'
import Layout from './components/Layout'

function ProtectedRoute({ children }) {
  const { token } = useAuth()
  return token ? children : <Navigate to="/login" />
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route index element={<ProjectsList />} />
              <Route path="projects" element={<Navigate to="/" replace />} />
              <Route path="overview" element={<CrossProjectOverview />} />
              <Route path="how-to" element={<HowTo />} />
              <Route path="projects/:slug" element={<ProjectDashboard />} />
              <Route path="projects/:slug/scans" element={<ScansList />} />
              <Route path="projects/:slug/scans/:scanId" element={<ScanDetail />} />
              <Route path="projects/:slug/rules" element={<RulesList />} />
              <Route path="projects/:slug/findings" element={<FindingsList />} />
              <Route path="projects/:slug/findings/:findingId" element={<FindingDetail />} />
              <Route path="projects/:slug/settings" element={<ProjectSettings />} />
              <Route path="projects/:slug/how-to" element={<HowTo />} />
            </Route>
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}
