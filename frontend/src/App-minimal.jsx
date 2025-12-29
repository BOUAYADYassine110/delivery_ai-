import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Welcome from './pages/Welcome'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import CreateOrder from './pages/CreateOrder'
import CreateInterCityOrder from './pages/CreateInterCityOrder'
import TrackOrder from './pages/TrackOrder'
import AgentMonitor from './pages/AgentMonitor'
import DriverDashboard from './pages/DriverDashboard'
import DriverLogin from './pages/DriverLogin'
import AdminLogin from './pages/AdminLogin'
import AdminDashboard from './pages/AdminDashboard'
import Navbar from './components/Navbar'

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token')
  return token && token !== 'undefined' ? children : <Navigate to="/login" />
}

function DriverProtectedRoute({ children }) {
  const token = localStorage.getItem('driver_token')
  return token && token !== 'undefined' ? children : <Navigate to="/driver/login" />
}

function AdminProtectedRoute({ children }) {
  const token = localStorage.getItem('admin_token')
  return token && token !== 'undefined' ? children : <Navigate to="/admin/login" />
}

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="p-8">
        <h1 className="text-3xl font-bold text-center mb-8">Multi-Agent Delivery System</h1>
        <div className="max-w-md mx-auto space-y-4">
          <a href="/login" className="block w-full bg-blue-500 text-white text-center py-2 px-4 rounded hover:bg-blue-600">
            Customer Login
          </a>
          <a href="/driver/login" className="block w-full bg-green-500 text-white text-center py-2 px-4 rounded hover:bg-green-600">
            Driver Login
          </a>
          <a href="/admin/login" className="block w-full bg-red-500 text-white text-center py-2 px-4 rounded hover:bg-red-600">
            Admin Login
          </a>
        </div>
      </div>
    </div>
  )
}

export default App