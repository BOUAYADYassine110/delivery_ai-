import React, { useState, useEffect, useRef } from 'react'
import routingService from '../services/routingService'
import gpsService from '../services/gpsService'

const AdvancedRouteDisplay = ({ driverLocation, destinations, onRouteSelect }) => {
  const mapRef = useRef(null)
  const [bestRoute, setBestRoute] = useState(null)
  const [loading, setLoading] = useState(false)
  const [currentPosition, setCurrentPosition] = useState(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [isNavigating, setIsNavigating] = useState(false)
  const [map, setMap] = useState(null)
  const [currentMarker, setCurrentMarker] = useState(null)

  useEffect(() => {
    if (driverLocation && destinations?.length) {
      calculateBestRoute()
    }
  }, [driverLocation, destinations])

  useEffect(() => {
    if (bestRoute && mapRef.current) {
      initializeMap()
    }
  }, [bestRoute])

  useEffect(() => {
    if (isNavigating) {
      startGPSTracking()
    } else {
      stopGPSTracking()
    }
  }, [isNavigating])

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

  const startGPSTracking = () => {
    gpsService.startTracking((position) => {
      if (position) {
        setCurrentPosition(position)
        updateCurrentPosition(position)
        checkNavigationProgress(position)
      }
    })
  }

  const stopGPSTracking = () => {
    gpsService.stopTracking()
  }

  const updateCurrentPosition = (position) => {
    if (!map) return
    
    const L = window.L
    
    // Remove old marker
    if (currentMarker) {
      map.removeLayer(currentMarker)
    }
    
    // Add new current position marker
    const newMarker = L.marker([position.lat, position.lng], {
      icon: L.divIcon({
        html: '🔵',
        iconSize: [20, 20],
        className: 'current-position-marker'
      })
    }).addTo(map)
    
    setCurrentMarker(newMarker)
  }

  const checkNavigationProgress = (position) => {
    if (!bestRoute?.steps) return
    
    // Simple step detection based on distance
    bestRoute.steps.forEach((step, index) => {
      if (index > currentStep) {
        const stepCoords = step.coordinates?.[0]
        if (stepCoords) {
          const distance = gpsService.calculateDistance(
            position.lat, position.lng,
            stepCoords[1], stepCoords[0]
          )
          
          if (distance < 0.05) { // Within 50 meters
            setCurrentStep(index)
            speakInstruction(step.instruction)
          }
        }
      }
    })
  }

  const speakInstruction = (instruction) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(instruction)
      utterance.rate = 0.8
      utterance.pitch = 1
      speechSynthesis.speak(utterance)
    }
  }

  const initializeMap = () => {
    if (!mapRef.current || !bestRoute) return

    // Load Leaflet dynamically
    if (!window.L) {
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
      document.head.appendChild(link)

      const script = document.createElement('script')
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
      script.onload = createMap
      document.head.appendChild(script)
    } else {
      createMap()
    }
  }

  const createMap = () => {
    const L = window.L
    
    if (mapRef.current._leaflet_id) {
      mapRef.current._leaflet_id = null
    }
    mapRef.current.innerHTML = ''

    const newMap = L.map(mapRef.current).setView([driverLocation.lat, driverLocation.lng], 15)
    setMap(newMap)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(newMap)

    // Driver start marker
    L.marker([driverLocation.lat, driverLocation.lng], {
      icon: L.divIcon({
        html: '🚗',
        iconSize: [30, 30],
        className: 'driver-marker'
      })
    }).addTo(newMap).bindPopup('Start Location')

    // Destination marker
    L.marker([bestRoute.destination.lat, bestRoute.destination.lng], {
      icon: L.divIcon({
        html: '🏁',
        iconSize: [30, 30],
        className: 'destination-marker'
      })
    }).addTo(newMap).bindPopup('Destination')

    // Route line with arrows
    if (bestRoute.coordinates) {
      const routeCoords = bestRoute.coordinates.map(coord => [coord[1], coord[0]])
      
      // Main route line
      L.polyline(routeCoords, { 
        color: '#2563eb', 
        weight: 6,
        opacity: 0.8 
      }).addTo(newMap)
      
      // Add direction arrows
      addDirectionArrows(newMap, routeCoords, L)
      
      // Add step markers
      addStepMarkers(newMap, L)
    }

    const bounds = L.latLngBounds([
      [driverLocation.lat, driverLocation.lng],
      [bestRoute.destination.lat, bestRoute.destination.lng]
    ])
    newMap.fitBounds(bounds, { padding: [30, 30] })
  }

  const addDirectionArrows = (map, coords, L) => {
    for (let i = 0; i < coords.length - 1; i += 5) {
      const start = coords[i]
      const end = coords[i + 1] || coords[coords.length - 1]
      
      const bearing = calculateBearing(start, end)
      const midPoint = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2]
      
      L.marker(midPoint, {
        icon: L.divIcon({
          html: `<div style="transform: rotate(${bearing}deg); font-size: 16px;">➤</div>`,
          iconSize: [20, 20],
          className: 'arrow-marker'
        })
      }).addTo(map)
    }
  }

  const addStepMarkers = (map, L) => {
    if (!bestRoute.steps) return
    
    bestRoute.steps.forEach((step, index) => {
      if (step.coordinates && step.coordinates.length > 0) {
        const coord = step.coordinates[0]
        L.marker([coord[1], coord[0]], {
          icon: L.divIcon({
            html: `<div class="step-marker">${index + 1}</div>`,
            iconSize: [25, 25],
            className: 'step-number'
          })
        }).addTo(map).bindPopup(`Step ${index + 1}: ${step.instruction}`)
      }
    })
  }

  const calculateBearing = (start, end) => {
    const lat1 = start[0] * Math.PI / 180
    const lat2 = end[0] * Math.PI / 180
    const deltaLng = (end[1] - start[1]) * Math.PI / 180
    
    const x = Math.sin(deltaLng) * Math.cos(lat2)
    const y = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(deltaLng)
    
    return (Math.atan2(x, y) * 180 / Math.PI + 360) % 360
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
            <div className="grid grid-cols-3 gap-4 text-center mb-4">
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
            
            <div className="flex justify-center space-x-3">
              <button
                onClick={() => setIsNavigating(!isNavigating)}
                className={`px-4 py-2 rounded-lg font-medium ${
                  isNavigating 
                    ? 'bg-red-500 text-white hover:bg-red-600' 
                    : 'bg-green-500 text-white hover:bg-green-600'
                }`}
              >
                {isNavigating ? '⏹️ Stop Navigation' : '🧭 Start Navigation'}
              </button>
              
              {isNavigating && (
                <div className="flex items-center space-x-2 bg-white px-3 py-2 rounded-lg">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium">Live GPS</span>
                </div>
              )}
            </div>
          </div>

          <div ref={mapRef} className="h-80 w-full"></div>

          {bestRoute.steps && (
            <div className="p-4 border-t bg-gray-50">
              <div className="flex justify-between items-center mb-3">
                <h4 className="font-medium text-gray-900">Turn-by-Turn Directions</h4>
                {isNavigating && (
                  <div className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                    Step {currentStep + 1} of {bestRoute.steps.length}
                  </div>
                )}
              </div>
              
              {isNavigating && bestRoute.steps[currentStep] && (
                <div className="bg-yellow-100 border-l-4 border-yellow-500 p-3 mb-3">
                  <div className="flex items-center">
                    <span className="text-2xl mr-3">📢</span>
                    <div>
                      <p className="font-semibold text-gray-900">Next: {bestRoute.steps[currentStep].instruction}</p>
                      <p className="text-sm text-gray-600">{(bestRoute.steps[currentStep].distance / 1000).toFixed(1)} km</p>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="max-h-32 overflow-y-auto space-y-2">
                {bestRoute.steps.slice(0, 6).map((step, index) => (
                  <div key={index} className={`flex items-start space-x-3 text-sm p-2 rounded ${
                    isNavigating && index === currentStep ? 'bg-blue-100 border border-blue-300' : ''
                  }`}>
                    <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                      isNavigating && index === currentStep 
                        ? 'bg-blue-500 text-white' 
                        : index < currentStep 
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-300 text-gray-600'
                    }`}>
                      {index < currentStep ? '✓' : index + 1}
                    </span>
                    <div className="flex-1">
                      <p className={`${isNavigating && index === currentStep ? 'font-semibold' : ''}`}>
                        {step.instruction}
                      </p>
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