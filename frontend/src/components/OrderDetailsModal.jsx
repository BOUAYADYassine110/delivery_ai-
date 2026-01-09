import React from 'react'
import { X, Package, MapPin, User, Phone, Calendar, DollarSign, Truck, Weight, Box, Clock, CheckCircle, Sparkles } from 'lucide-react'

export default function OrderDetailsModal({ order, onClose }) {
  if (!order) return null

  const statusConfig = {
    pending: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', icon: Clock },
    pending_assignment: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', icon: Clock },
    pending_acceptance: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', icon: Clock },
    assigned: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', icon: Truck },
    accepted: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', icon: Truck },
    picked_up: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700', icon: Package },
    in_transit: { bg: 'bg-indigo-50', border: 'border-indigo-200', text: 'text-indigo-700', icon: Truck },
    delivered: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', icon: CheckCircle }
  }

  const config = statusConfig[order.status] || statusConfig.pending
  const StatusIcon = config.icon

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fadeIn" onClick={onClose}>
      <div className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl animate-slideUp" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="bg-gradient-to-br from-blue-600 via-blue-700 to-purple-700 text-white p-8">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <Package className="w-8 h-8" />
                <h2 className="text-3xl font-bold">Order Details</h2>
              </div>
              <p className="text-blue-100 font-mono text-lg tracking-wide">{order.tracking_number || order.id}</p>
            </div>
            <button 
              onClick={onClose} 
              className="p-2 hover:bg-white/20 rounded-xl transition-all duration-200 hover:rotate-90"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
          
          {/* Status Badge */}
          <div className="flex items-center justify-between mt-6">
            <div className={`flex items-center gap-2 px-5 py-3 rounded-2xl ${config.bg} ${config.border} border-2`}>
              <StatusIcon className={`w-5 h-5 ${config.text}`} />
              <span className={`font-bold ${config.text} uppercase tracking-wide`}>
                {order.status.replace(/_/g, ' ')}
              </span>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold">{order.price || order.total_cost} MAD</div>
              <div className="text-blue-100 capitalize flex items-center gap-1 justify-end">
                {order.service_type === 'express' && <Sparkles className="w-4 h-4" />}
                {order.service_type}
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-8 space-y-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {/* Sender & Receiver */}
          <div className="grid md:grid-cols-2 gap-6">
            <div className="group hover:shadow-lg transition-all duration-300 bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl p-6 border-2 border-blue-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-600 rounded-xl">
                  <User className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-bold text-gray-900 text-lg">Sender</h3>
              </div>
              <div className="space-y-3">
                <p className="font-semibold text-gray-900 text-lg">{order.sender_name}</p>
                <div className="flex items-center gap-2 text-gray-700">
                  <Phone className="w-4 h-4" />
                  <span className="font-medium">{order.sender_phone}</span>
                </div>
                <div className="flex items-start gap-2 text-gray-700">
                  <MapPin className="w-4 h-4 mt-1 flex-shrink-0" />
                  <span className="font-medium">{order.pickup_address}, {order.pickup_city}</span>
                </div>
              </div>
            </div>

            <div className="group hover:shadow-lg transition-all duration-300 bg-gradient-to-br from-green-50 to-green-100 rounded-2xl p-6 border-2 border-green-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-green-600 rounded-xl">
                  <MapPin className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-bold text-gray-900 text-lg">Receiver</h3>
              </div>
              <div className="space-y-3">
                <p className="font-semibold text-gray-900 text-lg">{order.receiver_name}</p>
                <div className="flex items-center gap-2 text-gray-700">
                  <Phone className="w-4 h-4" />
                  <span className="font-medium">{order.receiver_phone}</span>
                </div>
                <div className="flex items-start gap-2 text-gray-700">
                  <MapPin className="w-4 h-4 mt-1 flex-shrink-0" />
                  <span className="font-medium">{order.delivery_address}, {order.delivery_city}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Package Details */}
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl p-6 border-2 border-purple-200">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-purple-600 rounded-xl">
                <Package className="w-5 h-5 text-white" />
              </div>
              <h3 className="font-bold text-gray-900 text-lg">Package Information</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl p-4">
                <p className="text-gray-500 text-sm mb-2">Weight</p>
                <p className="font-bold text-gray-900 flex items-center gap-2 text-lg">
                  <Weight className="w-5 h-5 text-purple-600" />
                  {order.weight} kg
                </p>
              </div>
              {order.dimensions && (
                <div className="bg-white rounded-xl p-4">
                  <p className="text-gray-500 text-sm mb-2">Dimensions</p>
                  <p className="font-bold text-gray-900 flex items-center gap-2 text-lg">
                    <Box className="w-5 h-5 text-purple-600" />
                    {order.dimensions.length}×{order.dimensions.width}×{order.dimensions.height}
                  </p>
                </div>
              )}
              <div className="bg-white rounded-xl p-4">
                <p className="text-gray-500 text-sm mb-2">Type</p>
                <p className="font-bold text-gray-900 capitalize">{order.delivery_type?.replace('_', ' ') || 'Standard'}</p>
              </div>
              {order.package_description && (
                <div className="bg-white rounded-xl p-4 col-span-2 md:col-span-1">
                  <p className="text-gray-500 text-sm mb-2">Description</p>
                  <p className="font-bold text-gray-900">{order.package_description}</p>
                </div>
              )}
            </div>
          </div>

          {/* Driver Info */}
          {order.driver_name && (
            <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-2xl p-6 border-2 border-orange-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-orange-600 rounded-xl">
                  <Truck className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-bold text-gray-900 text-lg">Driver Information</h3>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                <div className="bg-white rounded-xl p-4">
                  <p className="text-gray-500 text-sm mb-2">Name</p>
                  <p className="font-bold text-gray-900">{order.driver_name}</p>
                </div>
                {order.driver_phone && (
                  <div className="bg-white rounded-xl p-4">
                    <p className="text-gray-500 text-sm mb-2">Phone</p>
                    <p className="font-bold text-gray-900">{order.driver_phone}</p>
                  </div>
                )}
                {order.vehicle_type && (
                  <div className="bg-white rounded-xl p-4">
                    <p className="text-gray-500 text-sm mb-2">Vehicle</p>
                    <p className="font-bold text-gray-900 capitalize">{order.vehicle_type}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Timeline & Price */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Timeline */}
            <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-6 border-2 border-gray-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-gray-700 rounded-xl">
                  <Calendar className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-bold text-gray-900 text-lg">Timeline</h3>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center bg-white rounded-xl p-3">
                  <span className="text-gray-600 font-medium">Created</span>
                  <span className="font-bold text-gray-900 text-sm">{new Date(order.created_at).toLocaleString()}</span>
                </div>
                {order.estimated_delivery && (
                  <div className="flex justify-between items-center bg-white rounded-xl p-3">
                    <span className="text-gray-600 font-medium">Est. Delivery</span>
                    <span className="font-bold text-gray-900 text-sm">{new Date(order.estimated_delivery).toLocaleString()}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Price Breakdown */}
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border-2 border-green-200">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-green-600 rounded-xl">
                  <DollarSign className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-bold text-gray-900 text-lg">Pricing</h3>
              </div>
              <div className="space-y-3">
                {order.pricing_method && (
                  <div className="flex items-center gap-2 bg-white rounded-xl p-3">
                    {order.pricing_method === 'ai_agent' && <Sparkles className="w-4 h-4 text-blue-600" />}
                    <span className="text-sm text-gray-600">
                      {order.pricing_method === 'ai_agent' ? '🤖 AI-Calculated' : 'Standard Formula'}
                    </span>
                  </div>
                )}
                <div className="bg-white rounded-xl p-4">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-gray-900 text-lg">Total</span>
                    <span className="font-bold text-green-600 text-2xl">{order.price || order.total_cost} MAD</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-2 capitalize">
                    {order.service_type} • {order.is_inter_city ? 'Inter-City' : 'Intra-City'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
