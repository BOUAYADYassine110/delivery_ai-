import React, { useState, useEffect } from 'react'
import { Package, TrendingUp, Clock, CheckCircle, Loader, Plus, Search, MapPin, Truck, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const [ordersData, setOrdersData] = useState([])
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState(null)
  
  useEffect(() => {
    // Get user from auth
    const auth = JSON.parse(localStorage.getItem('auth') || '{}')
    setUser(auth.user)

    // Fetch orders
    fetch('http://localhost:8001/api/orders')
      .then(res => res.json())
      .then(data => {
        setOrdersData(Array.isArray(data) ? data : [])
        setLoading(false)
      })
      .catch(err => {
        console.error('Error:', err)
        setOrdersData([])
        setLoading(false)
      })
  }, [])

  const stats = [
    { 
      label: 'Total Orders', 
      value: ordersData?.length || 0, 
      icon: Package, 
      color: 'blue',
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600',
      iconBg: 'bg-blue-600'
    },
    { 
      label: 'In Transit', 
      value: ordersData?.filter(o => o.status === 'in_transit').length || 0, 
      icon: TrendingUp, 
      color: 'purple',
      bgColor: 'bg-purple-50',
      textColor: 'text-purple-600',
      iconBg: 'bg-purple-600'
    },
    { 
      label: 'Pending', 
      value: ordersData?.filter(o => ['pending', 'pending_assignment'].includes(o.status)).length || 0, 
      icon: Clock, 
      color: 'orange',
      bgColor: 'bg-orange-50',
      textColor: 'text-orange-600',
      iconBg: 'bg-orange-600'
    },
    { 
      label: 'Delivered', 
      value: ordersData?.filter(o => o.status === 'delivered').length || 0, 
      icon: CheckCircle, 
      color: 'green',
      bgColor: 'bg-green-50',
      textColor: 'text-green-600',
      iconBg: 'bg-green-600'
    }
  ]

  const statusColors = {
    pending: 'badge-yellow',
    pending_assignment: 'badge-yellow',
    picked_up: 'badge-blue',
    in_transit: 'badge-purple',
    delivered: 'badge-green',
    accepted: 'badge-blue',
    assigned: 'badge-blue'
  }

  const recentOrders = ordersData?.slice(0, 5) || []

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white shadow-xl animate-fadeInUp">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              Welcome back, {user?.full_name || 'User'}! 👋
            </h1>
            <p className="text-blue-100">
              Track your deliveries and manage your shipments
            </p>
          </div>
          <Link 
            to="/create" 
            className="group px-6 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:shadow-xl transition-all duration-300 flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            New Order
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div 
            key={i} 
            className={`${stat.bgColor} rounded-2xl p-6 hover:shadow-lg transition-all duration-300 hover:-translate-y-1 animate-fadeInUp`}
            style={{animationDelay: `${i * 0.1}s`}}
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`w-12 h-12 ${stat.iconBg} rounded-xl flex items-center justify-center`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <div className={`text-3xl font-bold ${stat.textColor}`}>{stat.value}</div>
            </div>
            <div className="text-sm font-medium text-gray-700">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-3 gap-6 animate-fadeInUp" style={{animationDelay: '0.4s'}}>
        <Link 
          to="/create" 
          className="group bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
        >
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <Plus className="w-6 h-6 text-blue-600" />
          </div>
          <h3 className="font-bold text-lg mb-2">Create Order</h3>
          <p className="text-gray-600 text-sm">Send a new package</p>
        </Link>

        <Link 
          to="/track" 
          className="group bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
        >
          <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <Search className="w-6 h-6 text-green-600" />
          </div>
          <h3 className="font-bold text-lg mb-2">Track Order</h3>
          <p className="text-gray-600 text-sm">Find your package</p>
        </Link>

        <Link 
          to="/system/coverage" 
          className="group bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
        >
          <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
            <MapPin className="w-6 h-6 text-purple-600" />
          </div>
          <h3 className="font-bold text-lg mb-2">Coverage Map</h3>
          <p className="text-gray-600 text-sm">View service areas</p>
        </Link>
      </div>

      {/* Recent Orders */}
      <div className="bg-white rounded-2xl shadow-lg p-6 animate-fadeInUp" style={{animationDelay: '0.5s'}}>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Recent Orders</h2>
          {ordersData?.length > 5 && (
            <Link to="/track" className="text-blue-600 hover:text-blue-700 font-medium text-sm">
              View All →
            </Link>
          )}
        </div>
        
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader className="w-8 h-8 text-blue-600 animate-spin" />
          </div>
        ) : ordersData?.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Package className="w-10 h-10 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No orders yet</h3>
            <p className="text-gray-600 mb-6">Create your first order to get started</p>
            <Link to="/create" className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors">
              <Plus className="w-5 h-5" />
              Create Order
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {recentOrders.map((order, index) => (
              <div 
                key={order.id} 
                className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-4 flex-1">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Package className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Link 
                        to={`/track?tracking=${order.tracking_number}`} 
                        className="font-mono text-blue-600 hover:text-blue-700 font-semibold"
                      >
                        {order.tracking_number}
                      </Link>
                      <span className={statusColors[order.status] || 'badge-blue'}>
                        {order.status.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        {order.pickup_city} → {order.delivery_city}
                      </span>
                      <span>{new Date(order.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <div className="text-right flex-shrink-0 ml-4">
                  <div className="font-bold text-gray-900">{order.price} MAD</div>
                  <div className="text-xs text-gray-500 capitalize">{order.service_type}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Help Section */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-2xl p-8 border-2 border-purple-100 animate-fadeInUp" style={{animationDelay: '0.6s'}}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Need Help?</h3>
            <p className="text-gray-600">Our support team is here to assist you 24/7</p>
          </div>
          <button className="px-6 py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-700 transition-colors">
            Contact Support
          </button>
        </div>
      </div>
    </div>
  )
}
