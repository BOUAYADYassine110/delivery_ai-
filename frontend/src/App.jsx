import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute, PublicRoute } from './components/ProtectedRoute'
import Navbar from './components/Navbar'
import ErrorBoundary from './components/ErrorBoundary'
import Loading from './components/Loading'

// Lazy load pages for code splitting
const Welcome = lazy(() => import('./pages/Welcome'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const CreateOrder = lazy(() => import('./pages/CreateOrder'))
const TrackOrder = lazy(() => import('./pages/TrackOrder'))
const PricingCalculator = lazy(() => import('./pages/PricingCalculator'))
const DriverDashboard = lazy(() => import('./pages/DriverDashboard'))
const DriverLogin = lazy(() => import('./pages/DriverLogin'))
const AdminLogin = lazy(() => import('./pages/AdminLogin'))
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'))
const AdminOrders = lazy(() => import('./pages/AdminOrders'))
const AdminDrivers = lazy(() => import('./pages/AdminDrivers'))
const AdminWarehouses = lazy(() => import('./pages/AdminWarehouses'))
const AdminAnalytics = lazy(() => import('./pages/AdminAnalytics'))
const SystemCoverage = lazy(() => import('./pages/SystemCoverage'))
const DeliverySimulation = lazy(() => import('./pages/DeliverySimulation'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
      cacheTime: 10 * 60 * 1000,
    },
  },
})

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <Router>
          <AuthProvider>
            <div className="min-h-screen bg-gray-50">
              <Suspense fallback={<Loading />}>
                <Routes>
                  {/* Public routes */}
                  <Route path="/" element={<PublicRoute><Welcome /></PublicRoute>} />
                  <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
                  <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
                  <Route path="/driver/login" element={<PublicRoute><DriverLogin /></PublicRoute>} />
                  <Route path="/admin/login" element={<PublicRoute><AdminLogin /></PublicRoute>} />
                  
                  {/* Customer routes */}
                  <Route path="/dashboard" element={<ProtectedRoute allowedRoles={['customer']}><Dashboard /></ProtectedRoute>} />
                  <Route path="/create" element={<ProtectedRoute allowedRoles={['customer']}><CreateOrder /></ProtectedRoute>} />
                  <Route path="/track" element={<ProtectedRoute allowedRoles={['customer']}><TrackOrder /></ProtectedRoute>} />
                  <Route path="/pricing" element={<ProtectedRoute allowedRoles={['customer']}><PricingCalculator /></ProtectedRoute>} />
                  <Route path="/simulation/:orderId" element={<ProtectedRoute allowedRoles={['customer', 'admin']}><DeliverySimulation /></ProtectedRoute>} />
                  
                  {/* Driver routes */}
                  <Route path="/driver/dashboard" element={<ProtectedRoute allowedRoles={['driver']}><DriverDashboard /></ProtectedRoute>} />
                  
                  {/* Admin routes */}
                  <Route path="/admin/dashboard" element={<ProtectedRoute allowedRoles={['admin']}><AdminDashboard /></ProtectedRoute>} />
                  <Route path="/admin/orders" element={<ProtectedRoute allowedRoles={['admin']}><AdminOrders /></ProtectedRoute>} />
                  <Route path="/admin/drivers" element={<ProtectedRoute allowedRoles={['admin']}><AdminDrivers /></ProtectedRoute>} />
                  <Route path="/admin/warehouses" element={<ProtectedRoute allowedRoles={['admin']}><AdminWarehouses /></ProtectedRoute>} />
                  <Route path="/admin/analytics" element={<ProtectedRoute allowedRoles={['admin']}><AdminAnalytics /></ProtectedRoute>} />
                  
                  {/* Public info */}
                  <Route path="/system/coverage" element={<SystemCoverage />} />
                </Routes>
              </Suspense>
            </div>
          </AuthProvider>
        </Router>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
