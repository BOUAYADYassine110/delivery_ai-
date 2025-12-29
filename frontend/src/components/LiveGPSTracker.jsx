import { useState, useEffect, useRef } from 'react'
import { MapPin, Navigation, Clock, AlertCircle } from 'lucide-react'
import gpsService from '../services/gpsService'
import routingService from '../services/routingService'
import { api } from '../services/api'

export default function LiveGPSTracker({ orderId, pickupCoords, deliveryCoords, onLocationUpdate }) {
  const [isTracking, setIsTracking] = useState(false)
  const [currentLocation, setCurrentLocation] = useState(null)
  const [route, setRoute] = useState(null)
  const [eta, setEta] = useState(null)
  const [error, setError] = useState(null)
  const [geofenceStatus, setGeofenceStatus] = useState(null)
  const intervalRef = useRef(null)

  // Start GPS tracking
  const startTracking = async () => {
    try {
      setError(null)
      setIsTracking(true)

      // Get initial position
      const position = await gpsService.getCurrentPosition()
      setCurrentLocation(position)

      // Get route to pickup or delivery
      const targetCoords = geofenceStatus === 'at_pickup' ? deliveryCoords : pickupCoords
      if (targetCoords) {
        const routeData = await routingService.getRoute(
          position.lat, position.lng,
          targetCoords.lat, targetCoords.lng
        )
        setRoute(routeData)
      }

      // Start continuous tracking
      gpsService.startTracking((newPosition, gpsError) => {
        if (gpsError) {
          setError('GPS tracking failed: ' + gpsError.message)
          return
        }

        setCurrentLocation(newPosition)
        
        // Check geofences
        checkGeofences(newPosition)
        
        // Update ETA
        if (targetCoords) {
          const etaData = routingService.calculateETA(
            newPosition.lat, newPosition.lng,
            targetCoords.lat, targetCoords.lng
          )
          setEta(etaData)
        }

        // Send to backend
        if (onLocationUpdate) {
          onLocationUpdate(newPosition)
        }

        // Update server every 30 seconds
        updateServerLocation(newPosition)
      })

      // Set up periodic server updates
      intervalRef.current = setInterval(() => {
        if (currentLocation) {
          updateServerLocation(currentLocation)
        }
      }, 30000)

    } catch (err) {
      setError('Failed to start GPS tracking: ' + err.message)
      setIsTracking(false)
    }
  }

  // Stop GPS tracking
  const stopTracking = () => {
    gpsService.stopTracking()
    setIsTracking(false)
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  // Check if driver is within geofences
  const checkGeofences = (position) => {
    const pickupDistance = pickupCoords ? 
      gpsService.calculateDistance(position.lat, position.lng, pickupCoords.lat, pickupCoords.lng) * 1000 : null
    
    const deliveryDistance = deliveryCoords ? 
      gpsService.calculateDistance(position.lat, position.lng, deliveryCoords.lat, deliveryCoords.lng) * 1000 : null

    if (pickupDistance && pickupDistance <= 100) {
      setGeofenceStatus('at_pickup')
    } else if (deliveryDistance && deliveryDistance <= 100) {
      setGeofenceStatus('at_delivery')
    } else {
      setGeofenceStatus('in_transit')
    }
  }

  // Update server with current location
  const updateServerLocation = async (position) => {
    if (!orderId) return

    try {
      await api.updateDriverLocation('current_driver', {
        latitude: position.lat,
        longitude: position.lng,
        accuracy: position.accuracy,
        speed: position.speed,
        heading: position.heading
      })
    } catch (error) {
      console.error('Failed to update server location:', error)
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopTracking()
    }
  }, [])

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Navigation className="w-5 h-5 text-blue-600" />
          Live GPS Tracking
        </h3>
        
        <button
          onClick={isTracking ? stopTracking : startTracking}
          className={`px-4 py-2 rounded-lg font-medium ${
            isTracking 
              ? 'bg-red-100 text-red-700 hover:bg-red-200' 
              : 'bg-green-100 text-green-700 hover:bg-green-200'
          }`}
        >
          {isTracking ? 'Stop Tracking' : 'Start Tracking'}
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 rounded-lg">
          <AlertCircle className="w-5 h-5" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {currentLocation && (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <MapPin className="w-4 h-4" />
              <span>Current Position</span>
            </div>
            <div className="text-xs font-mono bg-gray-50 p-2 rounded">
              {currentLocation.lat.toFixed(6)}, {currentLocation.lng.toFixed(6)}
            </div>
            <div className="text-xs text-gray-500">
              Accuracy: ±{Math.round(currentLocation.accuracy)}m
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Clock className="w-4 h-4" />
              <span>Status</span>
            </div>
            <div className={`text-sm font-medium px-2 py-1 rounded ${
              geofenceStatus === 'at_pickup' ? 'bg-blue-100 text-blue-700' :
              geofenceStatus === 'at_delivery' ? 'bg-green-100 text-green-700' :
              'bg-yellow-100 text-yellow-700'
            }`}>
              {geofenceStatus === 'at_pickup' ? 'At Pickup Location' :
               geofenceStatus === 'at_delivery' ? 'At Delivery Location' :
               'In Transit'}
            </div>
            {currentLocation.speed > 0 && (
              <div className="text-xs text-gray-500">
                Speed: {Math.round(currentLocation.speed * 3.6)} km/h
              </div>
            )}
          </div>
        </div>
      )}

      {eta && (
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="text-sm font-medium text-blue-900">Estimated Arrival</div>
          <div className="text-lg font-bold text-blue-700">
            {new Date(eta.eta).toLocaleTimeString()}
          </div>
          <div className="text-xs text-blue-600">
            {eta.remainingDistance.toFixed(1)} km • {Math.round(eta.remainingTime)} min
          </div>
        </div>
      )}

      {route && (
        <div className="text-xs text-gray-500 space-y-1">
          <div>Route: {route.distance.toFixed(1)} km</div>
          <div>Duration: {Math.round(route.duration)} minutes</div>
        </div>
      )}
    </div>
  )
}