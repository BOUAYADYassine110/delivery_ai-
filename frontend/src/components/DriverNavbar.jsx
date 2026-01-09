import React, { useState, useEffect } from 'react'
import { Truck, Package, MapPin, Bell, LogOut, User, X, DollarSign } from 'lucide-react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function DriverNavbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showNotifications, setShowNotifications] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)

  const isActive = (path) => location.pathname === path

  useEffect(() => {
    fetchNotifications()
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('driver_token')
      if (!token) return

      const response = await fetch('http://localhost:8001/api/notifications', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (response.ok) {
        const data = await response.json()
        setNotifications(data.slice(0, 10))
        setUnreadCount(data.filter(n => !n.read).length)
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    }
  }

  const markAsRead = async (notificationId) => {
    try {
      const token = localStorage.getItem('driver_token')
      await fetch(`http://localhost:8001/api/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      fetchNotifications()
    } catch (error) {
      console.error('Failed to mark as read:', error)
    }
  }

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'order_assigned': return '📦'
      case 'order_accepted': return '✅'
      case 'pickup_ready': return '🏪'
      case 'delivery_completed': return '🎉'
      default: return '🔔'
    }
  }

  return (
    <nav className="bg-white shadow-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/driver/dashboard" className="flex items-center gap-2 group">
            <div className="w-10 h-10 bg-gradient-to-br from-green-600 to-green-700 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
              <Truck className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-green-600 to-green-700 bg-clip-text text-transparent">
              Driver Portal
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-1">
            <Link
              to="/driver/dashboard"
              className={`px-4 py-2 rounded-lg transition-all font-medium ${
                isActive('/driver/dashboard')
                  ? 'bg-green-50 text-green-600'
                  : 'text-gray-700 hover:text-green-600 hover:bg-green-50'
              }`}
            >
              Dashboard
            </Link>
            <Link
              to="/driver/orders"
              className={`px-4 py-2 rounded-lg transition-all font-medium flex items-center gap-2 ${
                isActive('/driver/orders')
                  ? 'bg-green-50 text-green-600'
                  : 'text-gray-700 hover:text-green-600 hover:bg-green-50'
              }`}
            >
              <Package className="w-4 h-4" />
              My Orders
            </Link>
            <Link
              to="/driver/routes"
              className={`px-4 py-2 rounded-lg transition-all font-medium flex items-center gap-2 ${
                isActive('/driver/routes')
                  ? 'bg-green-50 text-green-600'
                  : 'text-gray-700 hover:text-green-600 hover:bg-green-50'
              }`}
            >
              <MapPin className="w-4 h-4" />
              Routes
            </Link>
            <Link
              to="/driver/earnings"
              className={`px-4 py-2 rounded-lg transition-all font-medium flex items-center gap-2 ${
                isActive('/driver/earnings')
                  ? 'bg-green-50 text-green-600'
                  : 'text-gray-700 hover:text-green-600 hover:bg-green-50'
              }`}
            >
              <DollarSign className="w-4 h-4" />
              Earnings
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-lg transition-all"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>

              {showNotifications && (
                <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 py-2 animate-fadeIn max-h-[500px] overflow-y-auto">
                  <div className="px-4 py-2 border-b border-gray-100 flex items-center justify-between">
                    <h3 className="font-semibold text-gray-900">Notifications</h3>
                    <button onClick={() => setShowNotifications(false)} className="text-gray-400 hover:text-gray-600">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  {notifications.length === 0 ? (
                    <div className="px-4 py-8 text-center text-gray-500">
                      <Bell className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                      <p>No notifications</p>
                    </div>
                  ) : (
                    <div className="divide-y divide-gray-100">
                      {notifications.map((notif) => (
                        <div
                          key={notif.id}
                          className={`px-4 py-3 hover:bg-gray-50 transition-colors cursor-pointer ${
                            !notif.read ? 'bg-green-50' : ''
                          }`}
                          onClick={() => !notif.read && markAsRead(notif.id)}
                        >
                          <div className="flex items-start gap-3">
                            <span className="text-2xl">{getNotificationIcon(notif.type)}</span>
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-gray-900 text-sm">{notif.title}</p>
                              <p className="text-xs text-gray-600 mt-1">{notif.message}</p>
                              <p className="text-xs text-gray-400 mt-1">
                                {new Date(notif.created_at).toLocaleString()}
                              </p>
                            </div>
                            {!notif.read && (
                              <div className="w-2 h-2 bg-green-500 rounded-full flex-shrink-0 mt-2"></div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-all"
              >
                <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-green-600 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
                <span className="hidden md:block font-medium">{user?.name || user?.email || 'Driver'}</span>
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl border border-gray-200 py-2 animate-fadeIn">
                  <div className="px-4 py-2 border-b border-gray-100">
                    <p className="text-sm font-semibold text-gray-900">{user?.name || 'Driver'}</p>
                    <p className="text-xs text-gray-500">{user?.email}</p>
                  </div>
                  <button
                    onClick={() => {
                      logout()
                      navigate('/')
                    }}
                    className="w-full px-4 py-2 text-left text-red-600 hover:bg-red-50 transition-colors flex items-center gap-2"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
