import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { api } from '../services/api'
import { MapPin, Search, Package, Map, Clock, Navigation, Cloud } from 'lucide-react'
import RouteMap from '../components/RouteMap'
import PackageTracker from '../components/PackageTracker'

export default function TrackOrder() {
  const [trackingNumber, setTrackingNumber] = useState('')
  const [searchTrigger, setSearchTrigger] = useState(null)

  const { data: order, isLoading, refetch } = useQuery(
    ['order', searchTrigger],
    () => api.trackOrder(searchTrigger).then(res => res.data),
    { 
      enabled: !!searchTrigger,
      refetchInterval: (data) => {
        if (!data) return false
        return data.status === 'picked_up' || data.status === 'in_transit' ? 2000 : false
      }
    }
  )

  const { data: events } = useQuery(
    ['tracking', order?.id],
    () => api.getTrackingEvents(order.id).then(res => res.data),
    { enabled: !!order?.id }
  )

  const [weather, setWeather] = useState(null)

  useEffect(() => {
    if (order?.receiver_lat && order?.receiver_lng) {
      fetch(`https://api.open-meteo.com/v1/forecast?latitude=${order.receiver_lat}&longitude=${order.receiver_lng}&current=temperature_2m,weather_code,wind_speed_10m`)
        .then(res => res.json())
        .then(data => setWeather(data.current))
        .catch(() => {})
    }
  }, [order])

  useEffect(() => {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)

    const script = document.createElement('script')
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    document.body.appendChild(script)

    return () => {
      document.head.removeChild(link)
      document.body.removeChild(script)
    }
  }, [])

  const handleSearch = (e) => {
    e.preventDefault()
    setSearchTrigger(trackingNumber)
  }

  // Use real coordinates from order (fallback for old orders without coordinates)
  const pickup = order?.sender_lat && order?.sender_lng 
    ? { lat: order.sender_lat, lng: order.sender_lng } 
    : null
  const delivery = order?.receiver_lat && order?.receiver_lng 
    ? { lat: order.receiver_lat, lng: order.receiver_lng } 
    : null
  const currentLocation = order?.current_lat && order?.current_lng && order.status !== 'delivered' 
    ? { lat: order.current_lat, lng: order.current_lng } 
    : null

  console.log('Order data:', { pickup, delivery, currentLocation, status: order?.status })

  return (
    <div className="animate-fade-in">
      <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-8">Track Your Order</h1>

      <div className="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl shadow-xl p-8 mb-8">
        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-white/70 w-5 h-5" />
            <input
              type="text"
              placeholder="Enter tracking number"
              value={trackingNumber}
              onChange={(e) => setTrackingNumber(e.target.value)}
              className="w-full pl-12 pr-4 py-4 bg-white/20 backdrop-blur-lg border-2 border-white/30 rounded-xl text-white placeholder-white/70 focus:bg-white/30 focus:outline-none focus:ring-4 focus:ring-white/30 transition-all"
            />
          </div>
          <button
            type="submit"
            className="bg-white text-blue-600 px-8 py-4 rounded-xl hover:bg-blue-50 font-semibold shadow-lg transform hover:scale-105 transition-all duration-300"
          >
            Track
          </button>
        </form>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      )}

      {order && (
        <PackageTracker 
          trackingNumber={trackingNumber}
          orderId={order.id}
        />
      )}

      {order && false && (
        <div className="space-y-6 animate-fade-in">
          {/* Delivery Type Badge */}
          <div className="mb-4">
            <span className={`inline-flex items-center gap-2 px-6 py-3 rounded-full font-bold text-lg shadow-lg ${
              order.delivery_type === 'intra_city' 
                ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white' 
                : 'bg-gradient-to-r from-purple-500 to-indigo-600 text-white'
            }`}>
              {order.delivery_type === 'intra_city' ? '🏙️ Intra-City Delivery' : '🚚 Inter-City Delivery'}
              {order.sender_city && order.receiver_city && (
                <span className="text-sm opacity-90">({order.sender_city} → {order.receiver_city})</span>
              )}
            </span>
          </div>

          {/* Route Info Cards */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-6 text-white shadow-lg">
              <div className="flex items-center gap-3 mb-2">
                <Navigation className="w-6 h-6" />
                <h4 className="font-semibold">Distance</h4>
              </div>
              <p className="text-3xl font-bold">{order.route_distance ? (order.route_distance / 1000).toFixed(1) : '—'} km</p>
            </div>
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-6 text-white shadow-lg">
              <div className="flex items-center gap-3 mb-2">
                <Clock className="w-6 h-6" />
                <h4 className="font-semibold">Est. Duration</h4>
              </div>
              <p className="text-3xl font-bold">{order.route_duration ? Math.round(order.route_duration / 60) : '—'} min</p>
            </div>
            <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl p-6 text-white shadow-lg">
              <div className="flex items-center gap-3 mb-2">
                <Cloud className="w-6 h-6" />
                <h4 className="font-semibold">Weather</h4>
              </div>
              <p className="text-3xl font-bold">{weather ? `${Math.round(weather.temperature_2m)}°C` : '—'}</p>
              {weather && <p className="text-sm mt-1 opacity-90">Wind: {Math.round(weather.wind_speed_10m)} km/h</p>}
            </div>
          </div>

          {/* Route Map */}
          {pickup && delivery ? (
            <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
              <div className="flex items-center gap-2 mb-4">
                <Map className="w-6 h-6 text-blue-600" />
                <h3 className="text-2xl font-bold text-gray-800">Delivery Route</h3>
              </div>
              <RouteMap
                pickup={pickup}
                delivery={delivery}
                currentLocation={currentLocation}
                routeGeometry={order.route_geometry}
              />
            </div>
          ) : (
            <div className="bg-yellow-50 border-2 border-yellow-200 rounded-2xl p-6">
              <p className="text-yellow-800 font-medium">📍 Map unavailable for this order. Please create new orders using the map picker to enable route tracking.</p>
            </div>
          )}

          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100 hover:shadow-2xl transition-all duration-300">
            <div className="grid grid-cols-2 gap-8">
              <div className="space-y-2">
                <h3 className="font-semibold text-gray-500 text-sm uppercase tracking-wide">From</h3>
                <p className="text-xl font-bold text-gray-800">{order.sender_name}</p>
                <p className="text-gray-600 flex items-start gap-2">
                  <MapPin className="w-5 h-5 text-blue-500 mt-1" />
                  {order.sender_address}
                </p>
              </div>
              <div className="space-y-2">
                <h3 className="font-semibold text-gray-500 text-sm uppercase tracking-wide">To</h3>
                <p className="text-xl font-bold text-gray-800">{order.receiver_name}</p>
                <p className="text-gray-600 flex items-start gap-2">
                  <MapPin className="w-5 h-5 text-green-500 mt-1" />
                  {order.receiver_address}
                </p>
              </div>
            </div>
            <div className="mt-6 pt-6 border-t border-gray-200">
              <div className="flex justify-between items-center">
                <div>
                  <span className="text-gray-500 text-sm">Status:</span>
                  <span className="ml-3 px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-full font-semibold text-sm">{order.status}</span>
                </div>
                <div>
                  <span className="text-gray-500 text-sm">Current Location:</span>
                  <span className="ml-3 font-semibold text-gray-800">{order.current_location}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
            <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <Package className="w-6 h-6 text-blue-600" />
              Tracking History
            </h3>
            <div className="space-y-6">
              {events?.map((event, idx) => (
                <div key={event.id} className="flex gap-6 group">
                  <div className="flex flex-col items-center">
                    <div className={`w-4 h-4 rounded-full ${idx === 0 ? 'bg-gradient-to-r from-blue-500 to-indigo-600 animate-pulse' : 'bg-gray-300'} shadow-lg`} />
                    {idx !== events.length - 1 && <div className="w-0.5 h-full bg-gradient-to-b from-gray-300 to-transparent mt-2" />}
                  </div>
                  <div className="flex-1 pb-6">
                    <div className="flex justify-between items-start mb-2">
                      <p className="font-bold text-lg text-gray-800">{event.status}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(event.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <p className="text-gray-600 mb-2">{event.description}</p>
                    <p className="text-sm text-gray-500 flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-blue-500" /> 
                      {event.location} • <span className="text-blue-600 font-medium">{event.agent_name}</span>
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
