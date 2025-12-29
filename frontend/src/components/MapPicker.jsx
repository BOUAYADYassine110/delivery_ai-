import { useEffect, useRef, useState } from 'react'
import { MapPin } from 'lucide-react'

export default function MapPicker({ onLocationSelect, label, initialPosition }) {
  const mapRef = useRef(null)
  const [map, setMap] = useState(null)
  const [marker, setMarker] = useState(null)
  const [address, setAddress] = useState('')

  useEffect(() => {
    if (!mapRef.current || !window.L) return

    // Clear any existing map
    if (mapRef.current._leaflet_id) {
      mapRef.current._leaflet_id = undefined
    }

    // Initialize Leaflet map
    const L = window.L
    const newMap = L.map(mapRef.current, { attributionControl: false }).setView(initialPosition || [33.5731, -7.5898], 13)
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(newMap)

    setMap(newMap)

    return () => newMap.remove()
  }, [])

  useEffect(() => {
    if (!map) return

    const handleClick = async (e) => {
      const { lat, lng } = e.latlng
      
      // Remove old marker
      if (marker) marker.remove()
      
      // Add new marker
      const L = window.L
      const newMarker = L.marker([lat, lng]).addTo(map)
      setMarker(newMarker)

      // Reverse geocode
      try {
        const response = await fetch(
          `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`
        )
        const data = await response.json()
        const addr = data.display_name
        setAddress(addr)
        onLocationSelect({ lat, lng, address: addr })
      } catch (error) {
        const addr = `${lat.toFixed(4)}, ${lng.toFixed(4)}`
        setAddress(addr)
        onLocationSelect({ lat, lng, address: addr })
      }
    }

    map.on('click', handleClick)
    return () => map.off('click', handleClick)
  }, [map, marker, onLocationSelect])

  return (
    <div>
      <label className="block font-semibold mb-2">
        <MapPin className="inline w-4 h-4 mr-1" />
        {label}
      </label>
      <div ref={mapRef} className="h-64 rounded border mb-2" />
      {address && (
        <div className="text-sm text-gray-600 p-2 bg-gray-50 rounded">
          Selected: {address}
        </div>
      )}
    </div>
  )
}
