import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'

// Basic components
function Welcome() {
  return (
    <div style={{ padding: '20px', textAlign: 'center', fontFamily: 'Arial' }}>
      <h1>Multi-Agent Delivery System</h1>
      <div style={{ marginTop: '20px' }}>
        <a href="/login" style={{ margin: '10px', padding: '10px 20px', backgroundColor: '#007bff', color: 'white', textDecoration: 'none', borderRadius: '5px' }}>
          Login
        </a>
        <a href="/driver/login" style={{ margin: '10px', padding: '10px 20px', backgroundColor: '#28a745', color: 'white', textDecoration: 'none', borderRadius: '5px' }}>
          Driver Login
        </a>
      </div>
    </div>
  )
}

function Login() {
  const [credentials, setCredentials] = React.useState({ username: '', password: '' })
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const response = await fetch('http://localhost:8001/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      })
      const data = await response.json()
      if (data.access_token) {
        localStorage.setItem('token', data.access_token)
        window.location.href = '/dashboard'
      }
    } catch (error) {
      alert('Login failed')
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '400px', margin: '50px auto', fontFamily: 'Arial' }}>
      <h2>User Login</h2>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="text"
            placeholder="Username"
            value={credentials.username}
            onChange={(e) => setCredentials({...credentials, username: e.target.value})}
            style={{ width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
          />
        </div>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="password"
            placeholder="Password"
            value={credentials.password}
            onChange={(e) => setCredentials({...credentials, password: e.target.value})}
            style={{ width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
          />
        </div>
        <button type="submit" style={{ width: '100%', padding: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}>
          Login
        </button>
      </form>
      <p style={{ textAlign: 'center', marginTop: '10px', fontSize: '12px' }}>
        Test: testuser / test123
      </p>
    </div>
  )
}

function Dashboard() {
  const [orders, setOrders] = React.useState([])
  const [loading, setLoading] = React.useState(true)

  React.useEffect(() => {
    fetch('http://localhost:8001/api/orders')
      .then(res => res.json())
      .then(data => {
        setOrders(Array.isArray(data) ? data : [])
        setLoading(false)
      })
      .catch(() => {
        setOrders([])
        setLoading(false)
      })
  }, [])

  if (loading) return <div style={{ padding: '20px' }}>Loading...</div>

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Dashboard</h1>
        <button onClick={() => { localStorage.removeItem('token'); window.location.href = '/' }} 
                style={{ padding: '8px 16px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px' }}>
          Logout
        </button>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '20px' }}>
        <div style={{ padding: '15px', backgroundColor: 'white', border: '1px solid #ddd', borderRadius: '8px' }}>
          <h3>Total Orders</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{orders.length}</p>
        </div>
        <div style={{ padding: '15px', backgroundColor: 'white', border: '1px solid #ddd', borderRadius: '8px' }}>
          <h3>In Transit</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{orders.filter(o => o.status === 'in_transit').length}</p>
        </div>
        <div style={{ padding: '15px', backgroundColor: 'white', border: '1px solid #ddd', borderRadius: '8px' }}>
          <h3>Delivered</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{orders.filter(o => o.status === 'delivered').length}</p>
        </div>
      </div>

      <div style={{ backgroundColor: 'white', border: '1px solid #ddd', borderRadius: '8px', padding: '20px' }}>
        <h2>Recent Orders</h2>
        {orders.length === 0 ? (
          <p>No orders found</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #ddd' }}>
                <th style={{ padding: '10px', textAlign: 'left' }}>ID</th>
                <th style={{ padding: '10px', textAlign: 'left' }}>Status</th>
                <th style={{ padding: '10px', textAlign: 'left' }}>Price</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '10px' }}>{order.tracking_number || order.id}</td>
                  <td style={{ padding: '10px' }}>{order.status}</td>
                  <td style={{ padding: '10px' }}>{order.price || order.total_cost} MAD</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function DriverLogin() {
  const [credentials, setCredentials] = React.useState({ email: '', password: '' })
  
  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const response = await fetch('http://localhost:8001/api/driver/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      })
      const data = await response.json()
      if (data.access_token) {
        localStorage.setItem('driver_token', data.access_token)
        localStorage.setItem('driver_id', data.driver.id)
        window.location.href = '/driver/dashboard'
      }
    } catch (error) {
      alert('Login failed')
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '400px', margin: '50px auto', fontFamily: 'Arial' }}>
      <h2>Driver Login</h2>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="email"
            placeholder="Email"
            value={credentials.email}
            onChange={(e) => setCredentials({...credentials, email: e.target.value})}
            style={{ width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
          />
        </div>
        <div style={{ marginBottom: '15px' }}>
          <input
            type="password"
            placeholder="Password"
            value={credentials.password}
            onChange={(e) => setCredentials({...credentials, password: e.target.value})}
            style={{ width: '100%', padding: '10px', border: '1px solid #ccc', borderRadius: '4px' }}
          />
        </div>
        <button type="submit" style={{ width: '100%', padding: '10px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px' }}>
          Login
        </button>
      </form>
      <p style={{ textAlign: 'center', marginTop: '10px', fontSize: '12px' }}>
        Test: driver@example.com / driver123
      </p>
    </div>
  )
}

function DriverDashboard() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h1>Driver Dashboard</h1>
        <button onClick={() => { localStorage.removeItem('driver_token'); window.location.href = '/' }} 
                style={{ padding: '8px 16px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px' }}>
          Logout
        </button>
      </div>
      <div style={{ backgroundColor: 'white', border: '1px solid #ddd', borderRadius: '8px', padding: '20px' }}>
        <h2>Welcome Driver!</h2>
        <p>Driver dashboard is working</p>
      </div>
    </div>
  )
}

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/login" />
}

function DriverProtectedRoute({ children }) {
  const token = localStorage.getItem('driver_token')
  return token ? children : <Navigate to="/driver/login" />
}

function App() {
  return (
    <Router>
      <div style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
        <Routes>
          <Route path="/" element={<Welcome />} />
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/driver/login" element={<DriverLogin />} />
          <Route path="/driver/dashboard" element={<DriverProtectedRoute><DriverDashboard /></DriverProtectedRoute>} />
        </Routes>
      </div>
    </Router>
  )
}

export default App