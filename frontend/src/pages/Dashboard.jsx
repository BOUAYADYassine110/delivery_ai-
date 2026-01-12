import React, { useState, useEffect } from 'react'
import { Package, TrendingUp, Clock, CheckCircle, Loader, Plus, MapPin, ArrowRight, Play, Eye } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import CustomerNavbar from '../components/CustomerNavbar'
import OrderDetailsModal from '../components/OrderDetailsModal'

export default function Dashboard() {
  const [ordersData, setOrdersData] = useState([])
  const [loading, setLoading] = useState(true)
  const { user, logout } = useAuth()
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [showAllOrders, setShowAllOrders] = useState(false)
  
  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      setLoading(false)
      return
    }

    fetch('http://localhost:8001/api/orders', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => {
        if (res.status === 401) {
          logout()
          return
        }
        return res.json()
      })
      .then(data => {
        if (data) setOrdersData(Array.isArray(data) ? data : [])
        setLoading(false)
      })
      .catch(err => {
        console.error('Error:', err)
        setOrdersData([])
        setLoading(false)
      })
  }, [])

  const stats = [
    { label: 'Total Orders', value: ordersData?.length || 0, icon: Package, bgColor: 'bg-blue-50', textColor: 'text-blue-600', iconBg: 'bg-blue-600' },
    { label: 'In Transit', value: ordersData?.filter(o => o.status === 'in_transit').length || 0, icon: TrendingUp, bgColor: 'bg-green-50', textColor: 'text-green-600', iconBg: 'bg-green-600' },
    { label: 'Pending', value: ordersData?.filter(o => ['pending', 'pending_assignment'].includes(o.status)).length || 0, icon: Clock, bgColor: 'bg-amber-50', textColor: 'text-amber-600', iconBg: 'bg-amber-600' },
    { label: 'Delivered', value: ordersData?.filter(o => o.status === 'delivered').length || 0, icon: CheckCircle, bgColor: 'bg-slate-50', textColor: 'text-slate-600', iconBg: 'bg-slate-600' }
  ]

  const statusColors = {
    pending: 'bg-amber-100 text-amber-700 px-3 py-1 rounded-full text-xs font-semibold',
    pending_assignment: 'bg-amber-100 text-amber-700 px-3 py-1 rounded-full text-xs font-semibold',
    picked_up: 'bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold',
    in_transit: 'bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-semibold',
    delivered: 'bg-slate-100 text-slate-700 px-3 py-1 rounded-full text-xs font-semibold',
    accepted: 'bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold',
    assigned: 'bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold'
  }

  const recentOrders = showAllOrders ? ordersData : (ordersData?.slice(0, 5) || [])

  return (
    <div className="min-h-screen bg-gray-50">
      <CustomerNavbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Welcome Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-2xl p-8 text-white shadow-xl">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold mb-2">Welcome back, {user?.full_name || user?.username || 'User'}! 👋</h1>
                <p className="text-blue-100">Track your deliveries and manage your shipments</p>
              </div>
              <Link to="/create" className="group px-6 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-blue-50 hover:shadow-xl transition-all duration-300 flex items-center justify-center gap-2 w-full md:w-auto">
                <Plus className="w-5 h-5" />
                New Order
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, i) => (
              <div key={i} className={`${stat.bgColor} rounded-2xl p-6 hover:shadow-lg transition-all duration-300 hover:-translate-y-1`}>
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

          {/* Recent Orders */}
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className="px-6 py-5 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">Recent Orders</h2>
                {ordersData?.length > 5 && (
                  <button 
                    onClick={() => setShowAllOrders(!showAllOrders)}
                    className="text-blue-600 hover:text-blue-700 font-medium text-sm flex items-center gap-1"
                  >
                    {showAllOrders ? 'Show Less' : 'View All'} <ArrowRight className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
            
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <Loader className="w-8 h-8 text-blue-600 animate-spin" />
              </div>
            ) : ordersData?.length === 0 ? (
              <div className="text-center py-16 px-6">
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
              <div className="divide-y divide-gray-100">
                {recentOrders.map((order) => (
                  <div key={order.id} className="p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex flex-col lg:flex-row lg:items-center gap-4">
                      {/* Order Icon & Info */}
                      <div className="flex items-start gap-4 flex-1 min-w-0">
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                          <Package className="w-6 h-6 text-blue-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-2">
                            <Link to={`/track?tracking=${order.tracking_number}`} className="font-mono text-blue-600 hover:text-blue-700 font-semibold text-sm">
                              {order.tracking_number}
                            </Link>
                            <span className={statusColors[order.status] || statusColors.pending}>
                              {order.status.replace('_', ' ')}
                            </span>
                          </div>
                          <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-sm text-gray-600">
                            <span className="flex items-center gap-1">
                              <MapPin className="w-4 h-4 flex-shrink-0" />
                              <span className="truncate">{order.pickup_city} → {order.delivery_city}</span>
                            </span>
                            <span className="text-gray-400">•</span>
                            <span>{new Date(order.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>

                      {/* Price & Actions */}
                      <div className="flex items-center gap-3 lg:flex-shrink-0">
                        <div className="text-right">
                          <div className="text-xl font-bold text-gray-900">{order.price} MAD</div>
                          <div className="text-xs text-gray-500 capitalize">{order.service_type}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setSelectedOrder(order)}
                            className="px-4 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-all flex items-center gap-2 font-medium text-sm shadow-sm hover:shadow-md"
                          >
                            <Eye className="w-4 h-4" />
                            <span className="hidden sm:inline">Details</span>
                          </button>
                          {order.status !== 'delivered' && (
                            <Link to={`/simulation/${order.id}`} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all flex items-center gap-2 font-medium text-sm shadow-sm hover:shadow-md">
                              <Play className="w-4 h-4" />
                              <span className="hidden sm:inline">Simulate</span>
                            </Link>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {selectedOrder && (
        <OrderDetailsModal order={selectedOrder} onClose={() => setSelectedOrder(null)} />
      )}
    </div>
  )
}
