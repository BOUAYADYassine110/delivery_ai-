import { useState, useEffect, useRef } from 'react'
import { MapPin, Package, Truck, Clock, Navigation } from 'lucide-react'

export default function PackageTracker({ trackingNumber, orderId }) {
  const [trackingData, setTrackingData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const wsRef = useRef(null)

  useEffect(() => {
    if (trackingNumber || orderId) {
      fetchTrackingData()
      setupWebSocket()
    }
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [trackingNumber, orderId])

  const fetchTrackingData = async () => {
    try {
      setLoading(true)
      const endpoint = trackingNumber 
        ? `/api/orders/tracking/${trackingNumber}`
        : `/api/orders/${orderId}/track`
      
      const response = await fetch(`http://localhost:8001${endpoint}`)
      const data = await response.json()
      
      if (response.ok) {
        setTrackingData(data)
        initializeMap(data)
      } else {
        setError(data.error || 'Order not found')
      }
    } catch (err) {
      setError('Failed to fetch tracking data')
    } finally {
      setLoading(false)
    }
  }

  const setupWebSocket = () => {
    const wsUrl = `ws://localhost:8001/ws/tracking/${orderId || trackingNumber}`
    wsRef.current = new WebSocket(wsUrl)
    
    wsRef.current.onmessage = (event) => {
      const update = JSON.parse(event.data)
      setTrackingData(prev => ({
        ...prev,
        order: {
          ...prev.order,
          status: update.status,
          current_location: update.current_location
        }
      }))
      updateMapLocation(update.current_location)
    }
  }

  const initializeMap = (data) => {
    if (!mapRef.current || !window.L || !data.pickup_coordinates) return

    const L = window.L
    const container = mapRef.current
    
    if (container._leaflet_id) {
      container._leaflet_id = undefined
      container.innerHTML = ''
    }

    const map = L.map(container).setView([data.pickup_coordinates.lat, data.pickup_coordinates.lng], 12)
    mapInstanceRef.current = map
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map)

    // Add markers based on order status and type
    addTrackingMarkers(map, data)
  }

  const addTrackingMarkers = (map, data) => {
    const L = window.L
    const order = data.order

    // Pickup marker
    const pickupIcon = L.divIcon({
      html: '<div style="background: #3b82f6; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><span style="color: white; font-size: 16px;">📦</span></div>',
      iconSize: [32, 32],
      iconAnchor: [16, 32]
    })

    L.marker([data.pickup_coordinates.lat, data.pickup_coordinates.lng], { icon: pickupIcon })
      .addTo(map)
      .bindPopup('<b>Pickup Location</b><br>' + order.pickup_address)

    // Delivery marker
    const deliveryIcon = L.divIcon({
      html: '<div style="background: #10b981; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><span style="color: white; font-size: 16px;">🏠</span></div>',
      iconSize: [32, 32],
      iconAnchor: [16, 32]
    })

    L.marker([data.delivery_coordinates.lat, data.delivery_coordinates.lng], { icon: deliveryIcon })
      .addTo(map)
      .bindPopup('<b>Delivery Location</b><br>' + order.delivery_address)

    // Current package location based on status
    const currentLocation = getCurrentPackageLocation(order, data)
    if (currentLocation) {
      const currentIcon = L.divIcon({
        html: '<div style="background: #f59e0b; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 4px solid white; box-shadow: 0 4px 12px rgba(0,0,0,0.4); animation: pulse 2s infinite;"><span style="color: white; font-size: 18px;">📍</span></div>',
        iconSize: [40, 40],
        iconAnchor: [20, 40]
      })

      L.marker([currentLocation.lat, currentLocation.lng], { icon: currentIcon })
        .addTo(map)
        .bindPopup('<b>Current Package Location</b><br>' + currentLocation.description)
    }

    // Warehouse markers for inter-city orders
    if (order.is_inter_city && data.warehouse_info) {
      const warehouseIcon = L.divIcon({
        html: '<div style="background: #8b5cf6; width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><span style="color: white; font-size: 16px;">🏢</span></div>',
        iconSize: [36, 36],
        iconAnchor: [18, 36]
      })

      // Origin warehouse
      if (data.warehouse_info.origin_warehouse) {
        L.marker([data.warehouse_info.origin_warehouse.lat, data.warehouse_info.origin_warehouse.lng], { icon: warehouseIcon })
          .addTo(map)
          .bindPopup('<b>Origin Warehouse</b><br>' + order.pickup_city)
      }

      // Destination warehouse
      if (data.warehouse_info.destination_warehouse) {
        L.marker([data.warehouse_info.destination_warehouse.lat, data.warehouse_info.destination_warehouse.lng], { icon: warehouseIcon })
          .addTo(map)
          .bindPopup('<b>Destination Warehouse</b><br>' + order.delivery_city)
      }
    }

    // Fit map to show all markers
    const group = new L.featureGroup()
    map.eachLayer(layer => {
      if (layer instanceof L.Marker) {
        group.addLayer(layer)
      }
    })
    map.fitBounds(group.getBounds().pad(0.1))
  }

  const getCurrentPackageLocation = (order, data) => {
    const status = order.status

    // For orders not yet picked up - package is at pickup location
    if (['pending_assignment', 'pending_acceptance', 'accepted', 'assigned'].includes(status)) {
      return {
        lat: data.pickup_coordinates.lat,
        lng: data.pickup_coordinates.lng,
        description: 'Package at pickup location'
      }
    }

    // For inter-city orders at warehouse
    if (order.is_inter_city) {
      if (['at_origin_warehouse', 'warehouse_processing'].includes(status)) {
        return {
          lat: data.warehouse_info?.origin_warehouse?.lat || data.pickup_coordinates.lat,
          lng: data.warehouse_info?.origin_warehouse?.lng || data.pickup_coordinates.lng,
          description: `Package at ${order.pickup_city} warehouse`
        }
      }
      
      if (['at_destination_warehouse'].includes(status)) {
        return {
          lat: data.warehouse_info?.destination_warehouse?.lat || data.delivery_coordinates.lat,
          lng: data.warehouse_info?.destination_warehouse?.lng || data.delivery_coordinates.lng,
          description: `Package at ${order.delivery_city} warehouse`
        }
      }
    }

    // For orders in transit - use driver's current location
    if (['picked_up', 'in_transit', 'in_transit_inter_city'].includes(status) && order.current_location) {
      return {
        lat: order.current_location.lat,
        lng: order.current_location.lng,
        description: 'Package with driver'
      }
    }

    // For delivered orders - package is at delivery location
    if (status === 'delivered') {
      return {
        lat: data.delivery_coordinates.lat,
        lng: data.delivery_coordinates.lng,
        description: 'Package delivered'
      }
    }

    return null
  }

  const updateMapLocation = (newLocation) => {
    if (!mapInstanceRef.current || !newLocation) return

    const L = window.L
    const map = mapInstanceRef.current

    // Remove existing current location marker
    map.eachLayer(layer => {
      if (layer.options && layer.options.isCurrentLocation) {
        map.removeLayer(layer)
      }
    })

    // Add new current location marker
    const currentIcon = L.divIcon({
      html: '<div style="background: #f59e0b; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 4px solid white; box-shadow: 0 4px 12px rgba(0,0,0,0.4); animation: pulse 2s infinite;"><span style="color: white; font-size: 18px;">📍</span></div>',
      iconSize: [40, 40],
      iconAnchor: [20, 40]
    })

    L.marker([newLocation.lat, newLocation.lng], { 
      icon: currentIcon,
      isCurrentLocation: true 
    })
      .addTo(map)
      .bindPopup('<b>Current Package Location</b>')
  }

  const getStatusColor = (status) => {
    const colors = {
      'pending_assignment': 'bg-yellow-100 text-yellow-800',
      'pending_acceptance': 'bg-yellow-100 text-yellow-800',
      'accepted': 'bg-blue-100 text-blue-800',
      'assigned': 'bg-blue-100 text-blue-800',
      'picked_up': 'bg-purple-100 text-purple-800',
      'in_transit': 'bg-orange-100 text-orange-800',
      'in_transit_inter_city': 'bg-orange-100 text-orange-800',
      'at_origin_warehouse': 'bg-indigo-100 text-indigo-800',
      'warehouse_processing': 'bg-indigo-100 text-indigo-800',
      'at_destination_warehouse': 'bg-indigo-100 text-indigo-800',
      'delivered': 'bg-green-100 text-green-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getProgressPercentage = (status) => {
    const progress = {
      'pending_assignment': 10,
      'pending_acceptance': 15,
      'accepted': 25,
      'assigned': 25,
      'picked_up': 40,
      'at_origin_warehouse': 50,
      'warehouse_processing': 55,
      'in_transit_inter_city': 70,
      'at_destination_warehouse': 80,
      'in_transit': 85,
      'delivered': 100
    }
    return progress[status] || 0
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center p-8">
        <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Tracking Not Found</h3>
        <p className="text-gray-600">{error}</p>
      </div>
    )
  }

  if (!trackingData) return null

  const { order, driver, tracking_events } = trackingData
  const progressPercentage = getProgressPercentage(order.status)

  return (
    <div className="space-y-6">
      {/* Order Header */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              {order.tracking_number || order.id}
            </h2>
            <p className="text-gray-600">
              {order.is_inter_city ? 'Inter-City' : 'Intra-City'} Delivery
            </p>
          </div>
          <div className="text-right">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(order.status)}`}>
              {order.status.replace('_', ' ').toUpperCase()}
            </span>
            <p className="text-sm text-gray-500 mt-1">
              {order.service_type} service
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{progressPercentage}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
        </div>

        {/* Addresses */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1">
              <Package className="w-4 h-4" />
              Pickup
            </div>
            <p className="text-gray-900">{order.pickup_address}</p>
            <p className="text-sm text-gray-500">{order.sender_name}</p>
          </div>
          <div>
            <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1">
              <MapPin className="w-4 h-4" />
              Delivery
            </div>
            <p className="text-gray-900">{order.delivery_address}</p>
            <p className="text-sm text-gray-500">{order.receiver_name}</p>
          </div>
        </div>
      </div>

      {/* Live Map */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Navigation className="w-5 h-5 text-blue-600" />
            Live Package Location
          </h3>
        </div>
        <div ref={mapRef} className="h-96 w-full"></div>
      </div>

      {/* Driver Info */}
      {driver && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Truck className="w-5 h-5 text-green-600" />
            Driver Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Driver</p>
              <p className="font-medium">{driver.name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Vehicle</p>
              <p className="font-medium">{driver.vehicle_type}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Rating</p>
              <p className="font-medium">⭐ {driver.rating}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tracking Events */}
      {tracking_events && tracking_events.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-purple-600" />
            Tracking History
          </h3>
          <div className="space-y-4">
            {tracking_events.map((event, index) => (
              <div key={index} className="flex items-start gap-4">
                <div className="flex-shrink-0 w-3 h-3 bg-blue-600 rounded-full mt-2"></div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-gray-900">{event.status}</h4>
                    <span className="text-sm text-gray-500">
                      {new Date(event.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{event.description}</p>
                  {event.location && (
                    <p className="text-xs text-gray-500">{event.location}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ETA */}
      {trackingData.estimated_arrival && order.status !== 'delivered' && (
        <div className="bg-blue-50 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            Estimated Delivery
          </h3>
          <p className="text-2xl font-bold text-blue-700">
            {new Date(trackingData.estimated_arrival).toLocaleString()}
          </p>
          {trackingData.distance && (
            <p className="text-sm text-blue-600 mt-1">
              Distance: {trackingData.distance} km
            </p>
          )}
        </div>
      )}
    </div>
  )
}