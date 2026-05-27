import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import UploadCenter from './pages/UploadCenter'
import ReviewDashboard from './pages/ReviewDashboard'
import RecordDetails from './pages/RecordDetails'
import AuditLogs from './pages/AuditLogs'
import Analytics from './pages/Analytics'

function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="upload" element={<UploadCenter />} />
          <Route path="review" element={<ReviewDashboard />} />
          <Route path="records/:id" element={<RecordDetails />} />
          <Route path="audit" element={<AuditLogs />} />
          <Route path="analytics" element={<Analytics />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
