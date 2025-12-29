import { useEffect, useRef, useState } from 'react'
import { Navigation, MapPin, Clock, AlertTriangle, Cloud } from 'lucide-react'
import routingService from '../services/routingService'

export default function OptimizedRouteMap({ pickupCoords, deliveryCoords, driverId, onRouteUpdate }) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const [route, setRoute] = useState(null)
  const [weather, setWeather] = useState(null)
  const [traffic, setTraffic] = useState('normal')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (pickupCoords && deliveryCoords) {
      initializeMap()
      fetchOptimizedRoute()
      fetchWeatherConditions()
    }
  }, [pickupCoords, deliveryCoords])

  const initializeMap = () => {
    if (!mapRef.current || !window.L) return

    const L = window.L
    const container = mapRef.current
    
    if (container._leaflet_id) {
      container._leaflet_id = undefined
      container.innerHTML = ''
    }

    const centerLat = (pickupCoords.lat + deliveryCoords.lat) / 2
    const centerLng = (pickupCoords.lng + deliveryCoords.lng) / 2
    
    const map = L.map(container).setView([centerLat, centerLng], 12)
    mapInstanceRef.current = map
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map)

    // Add pickup marker
    const pickupIcon = L.divIcon({
      html: '<div style="background: #3b82f6; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><span style="color: white; font-size: 16px;">📦</span></div>',
      iconSize: [32, 32],
      iconAnchor: [16, 32]
    })

    L.marker([pickupCoords.lat, pickupCoords.lng], { icon: pickupIcon })
      .addTo(map)
      .bindPopup('<b>Pickup Location</b>')

    // Add delivery marker
    const deliveryIcon = L.divIcon({
      html: '<div style="background: #10b981; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><span style="color: white; font-size: 16px;">🏠</span></div>',
      iconSize: [32, 32],
      iconAnchor: [16, 32]
    })

    L.marker([deliveryCoords.lat, deliveryCoords.lng], { icon: deliveryIcon })
      .addTo(map)
      .bindPopup('<b>Delivery Location</b>')
  }

  const fetchOptimizedRoute = async () => {
    try {
      setLoading(true)
      
      const routeData = await routingService.getRoute(
        pickupCoords.lat, pickupCoords.lng,
        deliveryCoords.lat, deliveryCoords.lng
      )
      
      setRoute(routeData)
      displayRoute(routeData)
      
      if (onRouteUpdate) {
        onRouteUpdate(routeData)
      }
      
    } catch (err) {
      setError('Failed to calculate route')
      console.error('Route calculation error:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchWeatherConditions = async () => {
    try {
      // Get weather for pickup location
      const response = await fetch(
        `https://api.open-meteo.com/v1/current?latitude=${pickupCoords.lat}&longitude=${pickupCoords.lng}&current=temperature_2m,precipitation,weather_code,wind_speed_10m`
      )
      const data = await response.json()
      
      const weatherData = {
        temperature: data.current.temperature_2m,
        precipitation: data.current.precipitation,
        weather_code: data.current.weather_code,
        wind_speed: data.current.wind_speed_10m,
        condition: getWeatherCondition(data.current.weather_code),
        is_rainy: data.current.precipitation > 0.1,
        is_stormy: data.current.wind_speed_10m > 25
      }
      
      setWeather(weatherData)
      
      // Simulate traffic based on weather
      if (weatherData.is_rainy) {
        setTraffic('heavy')
      } else if (weatherData.is_stormy) {
        setTraffic('severe')
      } else {
        setTraffic('normal')
      }
      
    } catch (err) {
      console.error('Weather fetch error:', err)
    }
  }

  const getWeatherCondition = (code) => {
    if ([61, 63, 65, 80, 81, 82].includes(code)) return 'rainy'
    if ([71, 73, 75, 85, 86].includes(code)) return 'snowy'
    if ([45, 48].includes(code)) return 'foggy'
    if ([95, 96, 99].includes(code)) return 'stormy'
    return 'clear'
  }

  const displayRoute = (routeData) => {
    if (!mapInstanceRef.current || !routeData.coordinates) return

    const L = window.L
    const map = mapInstanceRef.current

    // Remove existing route
    map.eachLayer(layer => {
      if (layer instanceof L.Polyline && layer.options.isRoute) {
        map.removeLayer(layer)
      }
    })

    // Convert coordinates for Leaflet (swap lng/lat)
    const routePoints = routeData.coordinates.map(coord => [coord[1], coord[0]])
    
    // Route color based on traffic conditions
    const routeColor = {
      'normal': '#3b82f6',
      'heavy': '#f59e0b',
      'severe': '#ef4444'
    }[traffic] || '#3b82f6'

    const routeLine = L.polyline(routePoints, {
      color: routeColor,
      weight: 6,
      opacity: 0.8,
      lineJoin: 'round',
      isRoute: true
    }).addTo(map)

    // Add route waypoints
    if (routeData.steps) {
      routeData.steps.forEach((step, index) => {
        if (step.coordinates && index % 3 === 0) { // Show every 3rd waypoint
          const waypointIcon = L.divIcon({
            html: `<div style="background: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid ${routeColor}; font-size: 12px; font-weight: bold;">${index + 1}</div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
          })

          L.marker([step.coordinates[1], step.coordinates[0]], { icon: waypointIcon })
            .addTo(map)
            .bindPopup(`<b>Step ${index + 1}</b><br>${step.instruction}`)
        }
      })
    }

    // Fit map to route
    map.fitBounds(routeLine.getBounds().pad(0.1))
  }

  const getTrafficColor = () => {
    switch (traffic) {
      case 'heavy': return 'text-yellow-600'
      case 'severe': return 'text-red-600'
      default: return 'text-green-600'
    }
  }

  const getWeatherIcon = () => {
    if (!weather) return '☀️'
    
    switch (weather.condition) {
      case 'rainy': return '🌧️'
      case 'snowy': return '❄️'
      case 'foggy': return '🌫️'
      case 'stormy': return '⛈️'
      default: return '☀️'
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Navigation className="w-5 h-5" />
            Optimized Route
          </h3>
          
          <div className="flex items-center gap-4 text-sm">
            {weather && (
              <div className="flex items-center gap-1">
                <span>{getWeatherIcon()}</span>
                <span>{Math.round(weather.temperature)}°C</span>
              </div>
            )}
            
            <div className={`flex items-center gap-1 ${getTrafficColor()}`}>
              <div className="w-2 h-2 rounded-full bg-current"></div>
              <span className="capitalize">{traffic} Traffic</span>
            </div>
          </div>
        </div>
      </div>

      {/* Route Info */}
      {route && (
        <div className="p-4 bg-gray-50 border-b">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {route.distance.toFixed(1)} km
              </div>
              <div className="text-sm text-gray-600">Distance</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {Math.round(route.duration)} min
              </div>
              <div className="text-sm text-gray-600">Duration</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">
                {route.steps ? route.steps.length : 0}
              </div>
              <div className="text-sm text-gray-600">Steps</div>
            </div>
          </div>
        </div>
      )}

      {/* Weather Alerts */}
      {weather && (weather.is_rainy || weather.is_stormy) && (
        <div className="p-3 bg-yellow-50 border-b border-yellow-200">
          <div className="flex items-center gap-2 text-yellow-800">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-sm font-medium">
              {weather.is_stormy ? 'Storm Warning: Drive carefully!' : 
               weather.is_rainy ? 'Rain Alert: Reduced visibility' : ''}
            </span>
          </div>
        </div>
      )}

      {/* Map */}
      <div className="relative">
        {loading && (
          <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}
        
        {error && (
          <div className="absolute inset-0 bg-red-50 flex items-center justify-center z-10">
            <div className="text-red-600 text-center">
              <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}
        
        <div ref={mapRef} className="h-96 w-full"></div>
      </div>

      {/* Turn-by-turn directions */}
      {route && route.steps && (
        <div className="p-4 max-h-48 overflow-y-auto">
          <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            Turn-by-turn Directions
          </h4>
          <div className="space-y-2">
            {route.steps.slice(0, 8).map((step, index) => (
              <div key={index} className="flex items-start gap-3 text-sm">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">
                  {index + 1}
                </div>
                <div className="flex-1">
                  <p className="text-gray-900">{step.instruction}</p>
                  {step.distance && (
                    <p className="text-gray-500 text-xs">
                      {step.distance > 1000 ? 
                        `${(step.distance / 1000).toFixed(1)} km` : 
                        `${Math.round(step.distance)} m`}
                    </p>
                  )}
                </div>
              </div>
            ))}
            {route.steps.length > 8 && (
              <div className="text-center text-gray-500 text-sm">
                ... and {route.steps.length - 8} more steps
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}