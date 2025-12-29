import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

// Import components with error boundaries
const Welcome = React.lazy(() => import('./pages/Welcome'));
const Login = React.lazy(() => import('./pages/Login'));
const AdminLogin = React.lazy(() => import('./pages/AdminLogin'));
const DriverLogin = React.lazy(() => import('./pages/DriverLogin'));
const SuperAdminDashboard = React.lazy(() => import('./pages/SuperAdminDashboard'));
const EnhancedDriverDashboard = React.lazy(() => import('./pages/EnhancedDriverDashboard'));

// Simple fallback components
const SimpleWelcome = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center max-w-4xl mx-auto px-4">
      <h1 className="text-5xl font-bold text-gray-900 mb-6">🚀 Multi-Agent Delivery System</h1>
      <p className="text-xl text-gray-600 mb-8">Advanced AI-powered delivery management system</p>
      
      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-bold mb-4">👤 Customer</h3>
          <a href="/login" className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 inline-block">
            Customer Login
          </a>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-bold mb-4">🚗 Driver</h3>
          <a href="/driver/login" className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 inline-block mb-2">
            Driver Login
          </a>
          <br />
          <a href="/driver/enhanced" className="bg-green-100 text-green-800 px-4 py-2 rounded text-sm hover:bg-green-200 inline-block">
            Enhanced Driver App
          </a>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-bold mb-4">⚙️ Admin</h3>
          <a href="/admin/login" className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 inline-block mb-2">
            Admin Login
          </a>
          <br />
          <a href="/admin/super" className="bg-purple-100 text-purple-800 px-4 py-2 rounded text-sm hover:bg-purple-200 inline-block">
            Super Admin Dashboard
          </a>
        </div>
      </div>
      
      <div className="mt-8 text-sm text-gray-500">
        <p>Test Credentials:</p>
        <p>Admin: admin / admin123</p>
        <p>Driver: driver@example.com / driver123</p>
        <p>Customer: testuser / test123</p>
      </div>
    </div>
  </div>
);

const SimpleLogin = ({ type = "user" }) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
      <h2 className="text-2xl font-bold mb-6 text-center">
        {type === "admin" ? "Admin Login" : type === "driver" ? "Driver Login" : "Customer Login"}
      </h2>
      <form>
        <input 
          type={type === "driver" ? "email" : "text"} 
          placeholder={type === "driver" ? "Email" : "Username"} 
          className="w-full p-3 border rounded mb-4" 
        />
        <input 
          type="password" 
          placeholder="Password" 
          className="w-full p-3 border rounded mb-4" 
        />
        <button 
          type="submit" 
          className={`w-full p-3 rounded text-white ${
            type === "admin" ? "bg-purple-600 hover:bg-purple-700" :
            type === "driver" ? "bg-green-600 hover:bg-green-700" :
            "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          Login
        </button>
      </form>
      <div className="mt-4 text-center text-sm text-gray-500">
        {type === "admin" && "Test: admin / admin123"}
        {type === "driver" && "Test: driver@example.com / driver123"}
        {type === "user" && "Test: testuser / test123"}
      </div>
      <div className="mt-4 text-center">
        <a href="/" className="text-blue-600 hover:text-blue-800 text-sm">← Back to Home</a>
      </div>
    </div>
  </div>
);

// Protected Route Components
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
}

function DriverProtectedRoute({ children }) {
  const token = localStorage.getItem('driver_token');
  return token ? children : <Navigate to="/driver/login" />;
}

function AdminProtectedRoute({ children }) {
  const token = localStorage.getItem('admin_token');
  return token ? children : <Navigate to="/admin/login" />;
}

// Error Boundary
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-600 mb-4">Something went wrong</h1>
            <button 
              onClick={() => window.location.reload()} 
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <React.Suspense fallback={
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading...</p>
              </div>
            </div>
          }>
            <Routes>
              <Route path="/" element={<SimpleWelcome />} />
              <Route path="/login" element={<SimpleLogin type="user" />} />
              <Route path="/admin/login" element={<SimpleLogin type="admin" />} />
              <Route path="/driver/login" element={<SimpleLogin type="driver" />} />
              
              {/* Try to load enhanced components, fallback to simple ones */}
              <Route path="/admin/super" element={
                <AdminProtectedRoute>
                  <SuperAdminDashboard />
                </AdminProtectedRoute>
              } />
              
              <Route path="/driver/enhanced" element={
                <DriverProtectedRoute>
                  <EnhancedDriverDashboard />
                </DriverProtectedRoute>
              } />
              
              {/* Fallback route */}
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </React.Suspense>
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;