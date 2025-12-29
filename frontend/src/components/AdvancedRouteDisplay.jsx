import React, { useState, useEffect, useRef } from 'react'
import routingService from '../services/routingService'

const AdvancedRouteDisplay = ({ driverLocation, destinations, onRouteSelect }) => {
  const mapRef = useRef(null)
  const [bestRoute, setBestRoute] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (driverLocation && destinations?.length) {
      calculateBestRoute()
    }
  }, [driverLocation, destinations])

  const calculateBestRoute = async () => {
    setLoading(true)
    try {
      const dest = destinations[0]
      const route = await routingService.getOptimalRoute(
        driverLocation.lat, driverLocation.lng,
        dest.lat, dest.lng,
        { vehicle: 'car' }
      )
      
      if (route) {
        setBestRoute({ ...route, destination: dest })
        onRouteSelect?.(route)
      }
    } catch (error) {
      console.error('Route calculation failed:', error)
    } finally {
      setLoading(false)
    }
  }



  const formatDuration = (minutes) => {
    const hours = Math.floor(minutes / 60)
    const mins = Math.round(minutes % 60)
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      <div className="p-4 bg-gray-50 border-b">
        <h3 className="text-lg font-semibold text-gray-900">🗺️ Best Route</h3>
        <p className="text-sm text-gray-600">Optimized delivery route</p>
      </div>

      {loading && (
        <div className="p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="text-sm text-gray-600 mt-2">Calculating best route...</p>
        </div>
      )}

      {bestRoute && (
        <>
          <div className="p-4 bg-blue-50 border-b">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-sm text-gray-600">Distance</p>
                <p className="text-lg font-bold text-blue-600">{bestRoute.distance.toFixed(1)} km</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Duration</p>
                <p className="text-lg font-bold text-green-600">{formatDuration(bestRoute.duration)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Score</p>
                <p className="text-lg font-bold text-purple-600">{Math.round(bestRoute.score || 90)}/100</p>
              </div>
            </div>
          </div>

          <div ref={mapRef} className="h-80 w-full bg-gray-100 flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">🗺️</div>
              <p className="text-lg font-semibold text-gray-700">Route: {bestRoute.destination.address}</p>
              <p className="text-sm text-gray-500 mt-2">Distance: {bestRoute.distance.toFixed(1)} km • Duration: {formatDuration(bestRoute.duration)}</p>
              <button 
                onClick={() => window.open(`https://www.google.com/maps/dir/${driverLocation.lat},${driverLocation.lng}/${bestRoute.destination.lat},${bestRoute.destination.lng}`, '_blank')}
                className="mt-4 bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600"
              >
                🧭 Open in Google Maps
              </button>
            </div>
          </div>

          {bestRoute.steps && (
            <div className="p-4 border-t bg-gray-50">
              <h4 className="font-medium text-gray-900 mb-3">Turn-by-Turn Directions</h4>
              <div className="max-h-32 overflow-y-auto space-y-2">
                {bestRoute.steps.slice(0, 4).map((step, index) => (
                  <div key={index} className="flex items-start space-x-3 text-sm">
                    <span className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs">
                      {index + 1}
                    </span>
                    <div className="flex-1">
                      <p className="text-gray-900">{step.instruction}</p>
                      <p className="text-gray-500">{(step.distance / 1000).toFixed(1)} km</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default AdvancedRouteDisplay