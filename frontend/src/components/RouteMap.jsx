import { useEffect, useRef } from 'react'

export default function RouteMap({ pickup, delivery, currentLocation, routeGeometry }) {
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const currentMarkerRef = useRef(null)

  if (!pickup || !delivery || !pickup.lat || !delivery.lat || !pickup.lng || !delivery.lng) {
    return (
      <div className="h-96 rounded-2xl bg-gray-100 flex items-center justify-center">
        <p className="text-gray-500">Map data unavailable</p>
      </div>
    )
  }

  // Initialize map once
  useEffect(() => {
    if (!mapRef.current || !window.L || mapInstanceRef.current) return

    const L = window.L
    const container = mapRef.current
    
    if (container._leaflet_id) {
      container._leaflet_id = undefined
      container.innerHTML = ''
    }

    const centerLat = (pickup.lat + delivery.lat) / 2
    const centerLng = (pickup.lng + delivery.lng) / 2
    
    const map = L.map(container, { attributionControl: false }).setView([centerLat, centerLng], 10)
    mapInstanceRef.current = map
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map)

    const pickupIcon = L.divIcon({
      html: '<div style="background: #3b82f6; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><svg width="16" height="16" fill="white" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/></svg></div>',
      className: '',
      iconSize: [32, 32],
      iconAnchor: [16, 32]
    })

    const deliveryIcon = L.divIcon({
      html: '<div style="background: #10b981; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"><svg width="16" height="16" fill="white" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/></svg></div>',
      className: '',
      iconSize: [32, 32],
      iconAnchor: [16, 32]
    })

    L.marker([pickup.lat, pickup.lng], { icon: pickupIcon })
      .addTo(map)
      .bindPopup('<div style="font-weight: bold; color: #3b82f6;">Pickup Location</div>')

    L.marker([delivery.lat, delivery.lng], { icon: deliveryIcon })
      .addTo(map)
      .bindPopup('<div style="font-weight: bold; color: #10b981;">Delivery Location</div>')

    if (routeGeometry && routeGeometry.length > 0) {
      const routePoints = routeGeometry.map(coord => [coord[1], coord[0]])
      L.polyline(routePoints, {
        color: '#6366f1',
        weight: 4,
        opacity: 0.7,
        lineJoin: 'round'
      }).addTo(map)
    } else {
      L.polyline([[pickup.lat, pickup.lng], [delivery.lat, delivery.lng]], {
        color: '#6366f1',
        weight: 4,
        opacity: 0.7,
        dashArray: '10, 10',
        lineJoin: 'round'
      }).addTo(map)
    }

    const bounds = L.latLngBounds([[pickup.lat, pickup.lng], [delivery.lat, delivery.lng]])
    map.fitBounds(bounds, { padding: [50, 50] })

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

  // Update only current location marker
  useEffect(() => {
    if (!mapInstanceRef.current || !window.L) return

    const L = window.L
    const map = mapInstanceRef.current

    // Remove old marker
    if (currentMarkerRef.current) {
      map.removeLayer(currentMarkerRef.current)
    }

    // Add new marker if location exists
    if (currentLocation?.lat && currentLocation?.lng) {
      const currentIcon = L.divIcon({
        html: '<div style="background: #f59e0b; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 4px solid white; box-shadow: 0 4px 12px rgba(0,0,0,0.4); animation: pulse 2s infinite;"><svg width="20" height="20" fill="white" viewBox="0 0 24 24"><path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3A8.994 8.994 0 0013 3.06V1h-2v2.06A8.994 8.994 0 003.06 11H1v2h2.06A8.994 8.994 0 0011 20.94V23h2v-2.06A8.994 8.994 0 0020.94 13H23v-2h-2.06zM12 19c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z"/></svg></div>',
        className: '',
        iconSize: [40, 40],
        iconAnchor: [20, 40]
      })

      currentMarkerRef.current = L.marker([currentLocation.lat, currentLocation.lng], { icon: currentIcon })
        .addTo(map)
        .bindPopup('<div style="font-weight: bold; color: #f59e0b;">Current Location</div>')
    }
  }, [currentLocation])

  return (
    <div className="relative">
      <div ref={mapRef} className="h-96 rounded-2xl shadow-xl border-4 border-white" />
      <div className="absolute top-4 right-4 bg-white/95 backdrop-blur-lg rounded-xl shadow-lg p-4 space-y-2">
        <div className="flex items-center gap-2 text-sm">
          <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
          <span className="font-medium">Pickup</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <div className="w-4 h-4 bg-green-500 rounded-full"></div>
          <span className="font-medium">Delivery</span>
        </div>
        {currentLocation?.lat && currentLocation?.lng && (
          <div className="flex items-center gap-2 text-sm">
            <div className="w-4 h-4 bg-orange-500 rounded-full animate-pulse"></div>
            <span className="font-medium">Current</span>
          </div>
        )}
      </div>
    </div>
  )
}
