import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider } from './components/Toast'
import ErrorBoundary from './components/ErrorBoundary'
import Login from './pages/Login'
import Register from './pages/Register'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
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
import AccountSettings from './pages/AccountSettings'
import TeamMembers from './pages/TeamMembers'
import Layout from './components/Layout'
import { ProjectLayout } from './context/ProjectContext'
import SessionTimeoutWarning from './components/SessionTimeoutWarning'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? children : <Navigate to="/login" />
}

function AuthenticatedApp({ children }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return children
  return (
    <>
      {children}
      <SessionTimeoutWarning />
    </>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <AuthenticatedApp>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                <Route index element={<ProjectsList />} />
                <Route path="projects" element={<Navigate to="/" replace />} />
                <Route path="overview" element={<CrossProjectOverview />} />
                <Route path="how-to" element={<HowTo />} />
                <Route path="settings/account" element={<AccountSettings />} />
                <Route path="projects/:slug" element={<ProjectLayout />}>
                  <Route index element={<ProjectDashboard />} />
                  <Route path="scans" element={<ScansList />} />
                  <Route path="scans/:scanId" element={<ScanDetail />} />
                  <Route path="rules" element={<RulesList />} />
                  <Route path="findings" element={<FindingsList />} />
                  <Route path="findings/:findingId" element={<FindingDetail />} />
                  <Route path="settings" element={<ProjectSettings />} />
                  <Route path="members" element={<TeamMembers />} />
                  <Route path="how-to" element={<HowTo />} />
                </Route>
              </Route>
            </Routes>
          </AuthenticatedApp>
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}
