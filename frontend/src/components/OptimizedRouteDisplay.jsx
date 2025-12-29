import { useState, useEffect, useRef } from 'react'
import { Navigation, MapPin, Clock, AlertTriangle, RefreshCw, Zap } from 'lucide-react'

export default function OptimizedRouteDisplay({ driverId, orders }) {
  const [routeData, setRouteData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    if (driverId && orders.length > 0) {
      fetchOptimizedRoute()
      
      // Auto-refresh every 5 minutes
      intervalRef.current = setInterval(fetchOptimizedRoute, 300000)
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [driverId, orders])

  useEffect(() => {
    if (routeData) {
      initializeMap()
    }
  }, [routeData])

  const fetchOptimizedRoute = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response = await fetch(`http://localhost:8001/api/route/driver/${driverId}/current`)
      const data = await response.json()
      
      if (data.success) {
        setRouteData(data.route)
        setLastUpdate(new Date())
      } else {
        setError(data.message || 'No route available')
      }
    } catch (err) {
      setError('Failed to fetch route')
      console.error('Route fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  const initializeMap = () => {
    if (!mapRef.current || !window.L || !routeData) return

    const L = window.L
    const container = mapRef.current
    
    if (container._leaflet_id) {
      container._leaflet_id = undefined
      container.innerHTML = ''
    }

    // Calculate map center from route coordinates
    const coords = routeData.coordinates
    if (!coords || coords.length === 0) return

    const centerLat = coords.reduce((sum, coord) => sum + coord[1], 0) / coords.length
    const centerLng = coords.reduce((sum, coord) => sum + coord[0], 0) / coords.length
    
    const map = L.map(container).setView([centerLat, centerLng], 13)
    mapInstanceRef.current = map
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map)

    // Draw optimized route
    drawOptimizedRoute(map, routeData)
    
    // Add waypoints
    if (routeData.waypoints) {
      addWaypoints(map, routeData.waypoints)
    }
  }

  const drawOptimizedRoute = (map, route) => {
    const L = window.L
    
    // Convert coordinates for Leaflet
    const routePoints = route.coordinates.map(coord => [coord[1], coord[0]])
    
    // Route color based on conditions
    let routeColor = '#3b82f6' // Default blue
    
    if (route.route_quality === 'poor') {
      routeColor = '#ef4444' // Red for poor conditions
    } else if (route.route_quality === 'fair') {
      routeColor = '#f59e0b' // Orange for fair conditions
    } else if (route.route_quality === 'excellent') {
      routeColor = '#10b981' // Green for excellent conditions
    }

    const routeLine = L.polyline(routePoints, {
      color: routeColor,
      weight: 6,
      opacity: 0.8,
      lineJoin: 'round'
    }).addTo(map)

    // Fit map to route
    map.fitBounds(routeLine.getBounds().pad(0.1))
  }

  const addWaypoints = (map, waypoints) => {
    const L = window.L
    
    waypoints.forEach((waypoint, index) => {
      const isPickup = waypoint.type === 'pickup'
      const iconColor = isPickup ? '#3b82f6' : '#10b981'
      const iconText = isPickup ? '📦' : '🏠'
      
      const waypointIcon = L.divIcon({
        html: `<div style="background: ${iconColor}; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3); position: relative;">
                 <span style="color: white; font-size: 16px;">${iconText}</span>
                 <div style="position: absolute; top: -8px; right: -8px; background: white; color: ${iconColor}; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; border: 2px solid ${iconColor};">${index + 1}</div>
               </div>`,
        iconSize: [36, 36],
        iconAnchor: [18, 36]
      })

      L.marker([waypoint.lat, waypoint.lng], { icon: waypointIcon })
        .addTo(map)
        .bindPopup(`
          <div style="min-width: 200px;">
            <h4 style="margin: 0 0 8px 0; color: ${iconColor}; font-weight: bold;">
              ${isPickup ? '📦 Pickup' : '🏠 Delivery'} #${index + 1}
            </h4>
            <p style="margin: 4px 0; font-size: 14px;"><strong>Address:</strong> ${waypoint.address}</p>
            <p style="margin: 4px 0; font-size: 14px;"><strong>Contact:</strong> ${waypoint.contact}</p>
            <p style="margin: 4px 0; font-size: 14px;"><strong>Phone:</strong> ${waypoint.phone}</p>
            <p style="margin: 4px 0; font-size: 12px; color: #666;">Order: ${waypoint.order_id}</p>
          </div>
        `)
    })
  }

  const getWeatherIcon = (condition) => {
    const icons = {
      'clear': '☀️',
      'rainy': '🌧️',
      'foggy': '🌫️',
      'stormy': '⛈️',
      'snowy': '❄️'
    }
    return icons[condition] || '☀️'
  }

  const getQualityColor = (quality) => {
    const colors = {
      'excellent': 'text-green-600',
      'good': 'text-blue-600',
      'fair': 'text-yellow-600',
      'poor': 'text-red-600'
    }
    return colors[quality] || 'text-gray-600'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center p-8">
        <AlertTriangle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Route Unavailable</h3>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={fetchOptimizedRoute}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    )
  }

  if (!routeData) return null

  return (
    <div className="space-y-6">
      {/* Route Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Navigation className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">Distance</span>
          </div>
          <div className="text-2xl font-bold text-blue-700">
            {(routeData.distance / 1000).toFixed(1)} km
          </div>
        </div>

        <div className="bg-purple-50 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-5 h-5 text-purple-600" />
            <span className="text-sm font-medium text-purple-900">Time</span>
          </div>
          <div className="text-2xl font-bold text-purple-700">
            {Math.round(routeData.optimized_duration / 60)} min
          </div>
          {routeData.original_duration !== routeData.optimized_duration && (
            <div className="text-xs text-purple-600">
              Optimized from {Math.round(routeData.original_duration / 60)} min
            </div>
          )}
        </div>

        <div className="bg-green-50 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-5 h-5 text-green-600" />
            <span className="text-sm font-medium text-green-900">Quality</span>
          </div>
          <div className={`text-lg font-bold capitalize ${getQualityColor(routeData.route_quality)}`}>
            {routeData.route_quality}
          </div>
        </div>

        <div className="bg-orange-50 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-lg">{getWeatherIcon(routeData.weather?.condition)}</span>
            <span className="text-sm font-medium text-orange-900">Weather</span>
          </div>
          <div className="text-lg font-bold text-orange-700">
            {routeData.weather?.temperature}°C
          </div>
          <div className="text-xs text-orange-600 capitalize">
            {routeData.weather?.condition}
          </div>
        </div>
      </div>

      {/* Warnings */}
      {routeData.warnings && routeData.warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="font-semibold text-yellow-800 mb-2 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Route Alerts
          </h4>
          <div className="space-y-1">
            {routeData.warnings.map((warning, index) => (
              <p key={index} className="text-sm text-yellow-700">{warning}</p>
            ))}
          </div>
        </div>
      )}

      {/* Interactive Map */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="p-4 bg-gray-50 border-b flex items-center justify-between">
          <h4 className="font-semibold text-gray-900 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-blue-600" />
            Live Route Map
          </h4>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchOptimizedRoute}
              className="p-2 text-gray-600 hover:text-blue-600 rounded-lg hover:bg-white"
              title="Refresh route"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            {lastUpdate && (
              <span className="text-xs text-gray-500">
                Updated: {lastUpdate.toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
        <div ref={mapRef} className="h-96 w-full"></div>
      </div>

      {/* Turn-by-turn Directions */}
      {routeData.steps && routeData.steps.length > 0 && (
        <div className="bg-white rounded-lg border">
          <div className="p-4 bg-gray-50 border-b">
            <h4 className="font-semibold text-gray-900">Turn-by-turn Directions</h4>
          </div>
          <div className="p-4 max-h-64 overflow-y-auto">
            <div className="space-y-3">
              {routeData.steps.slice(0, 10).map((step, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <p className="text-gray-900 font-medium">{step.instruction}</p>
                    {step.distance > 0 && (
                      <p className="text-sm text-gray-500">
                        {step.distance > 1000 ? 
                          `${(step.distance / 1000).toFixed(1)} km` : 
                          `${Math.round(step.distance)} m`}
                      </p>
                    )}
                  </div>
                </div>
              ))}
              {routeData.steps.length > 10 && (
                <div className="text-center text-gray-500 text-sm">
                  ... and {routeData.steps.length - 10} more steps
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Route Statistics */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-3">Route Statistics</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Avg Speed:</span>
            <span className="ml-2 font-medium">{routeData.optimized_speed} km/h</span>
          </div>
          <div>
            <span className="text-gray-600">Stops:</span>
            <span className="ml-2 font-medium">{routeData.waypoints?.length || 0}</span>
          </div>
          <div>
            <span className="text-gray-600">Traffic:</span>
            <span className="ml-2 font-medium capitalize">{routeData.traffic?.condition}</span>
          </div>
          <div>
            <span className="text-gray-600">Vehicle:</span>
            <span className="ml-2 font-medium capitalize">{routeData.vehicle_type}</span>
          </div>
        </div>
      </div>
    </div>
  )
}