import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import Navbar from './components/Navbar'

import Welcome from './pages/Welcome'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import CreateOrder from './pages/CreateOrder'
import TrackOrder from './pages/TrackOrder'
import AgentMonitor from './pages/AgentMonitor'
import DriverDashboard from './pages/DriverDashboard'
import DriverLogin from './pages/DriverLogin'
import AdminLogin from './pages/AdminLogin'
import AdminDashboard from './pages/AdminDashboard'
import SystemCoverage from './pages/SystemCoverage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 0,
      refetchOnWindowFocus: false,
      refetchOnMount: true,
      staleTime: 0,
      cacheTime: 0,
    },
  },
})

function checkAuth(key) {
  const auth = JSON.parse(localStorage.getItem(key) || '{}')
  if (auth.token && auth.expiry > Date.now()) {
    return true
  }
  localStorage.removeItem(key)
  return false
}

function ProtectedRoute({ children }) {
  return checkAuth('auth') ? children : <Navigate to="/login" />
}

function DriverProtectedRoute({ children }) {
  return checkAuth('driver_auth') ? children : <Navigate to="/driver/login" />
}

function AdminProtectedRoute({ children }) {
  return checkAuth('admin_auth') ? children : <Navigate to="/admin/login" />
}

function App() {
  const isAuthenticated = checkAuth('auth') || checkAuth('driver_auth') || checkAuth('admin_auth')

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          {isAuthenticated && <Navbar />}

          <main>
            <div className={isAuthenticated ? "max-w-7xl mx-auto px-4 py-8" : ""}>
              <Routes>
                <Route path="/" element={<Welcome />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                <Route path="/create" element={<ProtectedRoute><CreateOrder /></ProtectedRoute>} />
                <Route path="/track" element={<ProtectedRoute><TrackOrder /></ProtectedRoute>} />
                <Route path="/agents" element={<ProtectedRoute><AgentMonitor /></ProtectedRoute>} />
                <Route path="/driver/login" element={<DriverLogin />} />
                <Route path="/driver/dashboard" element={<DriverProtectedRoute><DriverDashboard /></DriverProtectedRoute>} />
                <Route path="/admin/login" element={<AdminLogin />} />
                <Route path="/admin/dashboard" element={<AdminProtectedRoute><AdminDashboard /></AdminProtectedRoute>} />
                <Route path="/system/coverage" element={<SystemCoverage />} />
              </Routes>
            </div>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  )
}

export default App
