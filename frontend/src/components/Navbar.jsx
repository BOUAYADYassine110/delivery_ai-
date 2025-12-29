import { Link } from 'react-router-dom'
import { Package, Plus, Search, Activity, LogOut, Truck, Menu, X } from 'lucide-react'
import { useState, useEffect } from 'react'

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [user, setUser] = useState(null)
  const [driver, setDriver] = useState(null)
  const [isDriver, setIsDriver] = useState(false)
  
  useEffect(() => {
    const checkAuth = () => {
      const auth = JSON.parse(localStorage.getItem('auth') || '{}')
      const driverAuth = JSON.parse(localStorage.getItem('driver_auth') || '{}')
      
      if (auth.token && auth.expiry > Date.now()) {
        setUser(auth.user)
        setIsDriver(false)
      } else if (driverAuth.token && driverAuth.expiry > Date.now()) {
        setDriver(driverAuth.driver)
        setIsDriver(true)
      } else {
        localStorage.removeItem('auth')
        localStorage.removeItem('driver_auth')
      }
    }
    
    checkAuth()
    window.addEventListener('storage', checkAuth)
    return () => window.removeEventListener('storage', checkAuth)
  }, [])
  
  const handleLogout = () => {
    if (isDriver) {
      localStorage.removeItem('driver_auth')
      window.location.href = '/driver/login'
    } else {
      localStorage.removeItem('auth')
      window.location.href = '/'
    }
  }

  const navItems = isDriver ? [
    { to: '/driver/dashboard', icon: Truck, label: 'My Deliveries' }
  ] : [
    { to: '/dashboard', icon: Activity, label: 'Dashboard' },
    { to: '/create', icon: Plus, label: 'Create Order' },
    { to: '/track', icon: Search, label: 'Track' },
    ...(user?.role === 'admin' || user?.role === 'employee' ? [
      { to: '/agents', icon: Activity, label: 'Agents' }
    ] : [])
  ]

  return (
    <nav className="bg-white shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to={isDriver ? '/driver/dashboard' : '/dashboard'} className="flex items-center gap-2">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Package className="w-6 h-6 text-white" />
            </div>
            <span className="font-bold text-xl text-gray-900">DeliveryAI</span>
          </Link>

          <div className="hidden md:flex items-center gap-2">
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
              >
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-4">
            <div className="text-right">
              <div className="font-semibold text-sm">{isDriver ? driver?.name : user?.full_name}</div>
              <div className="text-xs text-gray-500 capitalize">{isDriver ? 'Driver' : user?.role}</div>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 text-gray-700 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden py-4 space-y-2">
            {navItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-blue-50 rounded-lg transition-colors"
              >
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            ))}
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <LogOut className="w-5 h-5" />
              <span className="font-medium">Logout</span>
            </button>
          </div>
        )}
      </div>
    </nav>
  )
}
