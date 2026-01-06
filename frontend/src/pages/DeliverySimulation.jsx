import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { MapPin, Package, Truck, Clock, Navigation, Cloud, AlertTriangle, CheckCircle } from 'lucide-react'

export default function DeliverySimulation() {
  const { orderId } = useParams()
  const navigate = useNavigate()
  const mapRef = useRef(null)
  const [map, setMap] = useState(null)
  const [order, setOrder] = useState(null)
  const [driver, setDriver] = useState(null)
  const [driverMarker, setDriverMarker] = useState(null)
  const [simulationStatus, setSimulationStatus] = useState('initializing')
  const [currentStep, setCurrentStep] = useState(0)
  const [weather, setWeather] = useState(null)
  const [traffic, setTraffic] = useState('moderate')
  const [route, setRoute] = useState([])
  const [events, setEvents] = useState([])

  useEffect(() => {
    fetchOrderData()
  }, [orderId])

  useEffect(() => {
    if (order && driver) {
      loadMapLibrary()
    }
  }, [order, driver])

  const loadMapLibrary = () => {
    if (window.L) {
      initializeMap()
      return
    }

    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)

    const script = document.createElement('script')
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    script.onload = initializeMap
    document.body.appendChild(script)
  }

  const fetchOrderData = async () => {
    try {
      const auth = JSON.parse(localStorage.getItem('auth') || '{}')
      const response = await fetch(`http://localhost:8001/api/orders/${orderId}/track`, {
        headers: { 'Authorization': `Bearer ${auth.access_token}` }
      })
      const data = await response.json()
      
      if (data.error) {
        console.error('Order not found')
        return
      }
      
      setOrder(data.order)
      setDriver(data.driver)
      
      if (data.order && data.order.pickup_city) {
        const weatherRes = await fetch(`http://localhost:8001/api/weather/${data.order.pickup_city}`)
        const weatherData = await weatherRes.json()
        setWeather(weatherData)
      }
      
      setTraffic(['light', 'moderate', 'heavy'][Math.floor(Math.random() * 3)])
    } catch (error) {
      console.error('Error fetching order:', error)
    }
  }

  const initializeMap = () => {
    if (!mapRef.current || map || !window.L) return

    const newMap = window.L.map(mapRef.current).setView([33.5731, -7.5898], 12)
    
    window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(newMap)

    setMap(newMap)
  }

  const startSimulation = async () => {
    if (!order || !driver || !map) return

    setSimulationStatus('running')
    addEvent('Simulation started', 'info')

    // Get coordinates - ALWAYS use stored coordinates from order
    const driverStart = driver.current_location
    const pickupCoords = order.pickup_coordinates || { lat: 33.5731, lng: -7.5898 }
    const deliveryCoords = order.delivery_coordinates || { lat: 33.5831, lng: -7.5998 }
    
    console.log('Using coordinates:', { pickupCoords, deliveryCoords })

    // Check if inter-city
    const isInterCity = order.is_inter_city || order.pickup_city !== order.delivery_city

    if (isInterCity) {
      await simulateInterCityDelivery(driverStart, pickupCoords, deliveryCoords)
    } else {
      await simulateIntraCityDelivery(driverStart, pickupCoords, deliveryCoords)
    }
  }

  const simulateInterCityDelivery = async (driverStart, pickupCoords, deliveryCoords) => {
    // Get warehouse coordinates
    const originWarehouse = await getWarehouseCoords(order.pickup_city)
    const destWarehouse = await getWarehouseCoords(order.delivery_city)

    // Add all markers
    const warehouseOriginMarker = window.L.marker([originWarehouse.lat, originWarehouse.lng], {
      icon: createCustomIcon('🏭', 'purple')
    }).addTo(map).bindPopup(`${order.pickup_city} Warehouse`)

    const pickupMarker = window.L.marker([pickupCoords.lat, pickupCoords.lng], {
      icon: createCustomIcon('📦', 'blue')
    }).addTo(map).bindPopup(`Pickup: ${order.pickup_address}`)

    const warehouseDestMarker = window.L.marker([destWarehouse.lat, destWarehouse.lng], {
      icon: createCustomIcon('🏭', 'purple')
    }).addTo(map).bindPopup(`${order.delivery_city} Warehouse`)

    const deliveryMarker = window.L.marker([deliveryCoords.lat, deliveryCoords.lng], {
      icon: createCustomIcon('🏠', 'green')
    }).addTo(map).bindPopup(`Delivery: ${order.delivery_address}`)

    // Create driver marker
    const dMarker = window.L.marker([originWarehouse.lat, originWarehouse.lng], {
      icon: createCustomIcon(getVehicleIcon(driver.vehicle_type), 'orange')
    }).addTo(map).bindPopup(`Driver: ${driver.name}`)
    setDriverMarker(dMarker)

    // Fit bounds to show all points
    map.fitBounds([
      [originWarehouse.lat, originWarehouse.lng],
      [pickupCoords.lat, pickupCoords.lng],
      [destWarehouse.lat, destWarehouse.lng],
      [deliveryCoords.lat, deliveryCoords.lng]
    ])

    // Phase 1: Warehouse to Pickup (use OSRM)
    addEvent(`Driver leaving ${order.pickup_city} warehouse`, 'info')
    await updateOrderStatus('en_route_to_pickup')
    const toPickupRoute = await fetchRouteOSRM(originWarehouse, pickupCoords)
    drawSingleRoute(toPickupRoute, map, 'blue')
    await animateAlongRoute(dMarker, toPickupRoute)

    // Phase 2: At Pickup
    addEvent('Driver arrived at pickup location', 'success')
    await updateOrderStatus('at_pickup')
    await sleep(2000)
    addEvent('Package picked up', 'success')
    await updateOrderStatus('picked_up')
    await sleep(2000)

    // Phase 3: Pickup to Origin Warehouse (use OSRM)
    addEvent(`Returning to ${order.pickup_city} warehouse`, 'info')
    await updateOrderStatus('returning_to_warehouse')
    const backToWarehouseRoute = await fetchRouteOSRM(pickupCoords, originWarehouse)
    drawSingleRoute(backToWarehouseRoute, map, 'orange')
    await animateAlongRoute(dMarker, backToWarehouseRoute)

    // Phase 4: At Origin Warehouse
    addEvent(`Package at ${order.pickup_city} warehouse`, 'success')
    await updateOrderStatus('at_origin_warehouse')
    await sleep(3000)

    // Phase 5: Inter-city truck transport (use OSRM)
    addEvent('Loading package onto inter-city truck', 'info')
    await sleep(2000)
    
    // Create truck marker
    const truckMarker = window.L.marker([originWarehouse.lat, originWarehouse.lng], {
      icon: createCustomIcon('🚚', 'red')
    }).addTo(map).bindPopup('Inter-city Truck')
    dMarker.remove()
    
    addEvent(`Truck departing to ${order.delivery_city}`, 'info')
    await updateOrderStatus('in_transit_inter_city')
    const interCityRoute = await fetchRouteOSRM(originWarehouse, destWarehouse)
    drawSingleRoute(interCityRoute, map, 'red')
    await animateAlongRoute(truckMarker, interCityRoute)

    // Phase 6: At Destination Warehouse
    addEvent(`Package arrived at ${order.delivery_city} warehouse`, 'success')
    await updateOrderStatus('at_destination_warehouse')
    await sleep(3000)
    truckMarker.remove()

    // Check delivery option
    if (order.delivery_option === 'warehouse_pickup' || order.delivery_type === 'warehouse_pickup') {
      addEvent('Package ready for customer pickup at warehouse', 'success')
      await updateOrderStatus('delivered')
      setSimulationStatus('completed')
    } else {
      // Phase 7: Final delivery to door (use OSRM)
      addEvent('Assigning final delivery driver', 'info')
      await sleep(2000)
      
      const finalDriver = window.L.marker([destWarehouse.lat, destWarehouse.lng], {
        icon: createCustomIcon('🚗', 'orange')
      }).addTo(map).bindPopup('Final Delivery Driver')
      
      addEvent('Driver heading to delivery address', 'info')
      await updateOrderStatus('out_for_delivery')
      const finalRoute = await fetchRouteOSRM(destWarehouse, deliveryCoords)
      drawSingleRoute(finalRoute, map, 'green')
      await animateAlongRoute(finalDriver, finalRoute)

      addEvent('Package delivered to customer door!', 'success')
      await updateOrderStatus('delivered')
      setSimulationStatus('completed')
    }
    
    setTimeout(() => fetchOrderData(), 1000)
  }

  const simulateIntraCityDelivery = async (driverStart, pickupCoords, deliveryCoords) => {
    // Add markers
    const pickupMarker = window.L.marker([pickupCoords.lat, pickupCoords.lng], {
      icon: createCustomIcon('📦', 'blue')
    }).addTo(map).bindPopup(`Pickup: ${order.pickup_address}`)

    const deliveryMarker = window.L.marker([deliveryCoords.lat, deliveryCoords.lng], {
      icon: createCustomIcon('🏠', 'green')
    }).addTo(map).bindPopup(`Delivery: ${order.delivery_address}`)

    const dMarker = window.L.marker([driverStart.lat, driverStart.lng], {
      icon: createCustomIcon(getVehicleIcon(driver.vehicle_type), 'orange')
    }).addTo(map).bindPopup(`Driver: ${driver.name}`)
    setDriverMarker(dMarker)

    map.fitBounds([
      [driverStart.lat, driverStart.lng],
      [pickupCoords.lat, pickupCoords.lng],
      [deliveryCoords.lat, deliveryCoords.lng]
    ])

    const routeData = await fetchRoute(driverStart, pickupCoords, deliveryCoords)
    setRoute(routeData)
    drawRoute(routeData, map)
    await animateDelivery(dMarker, routeData, pickupCoords, deliveryCoords)
  }

  const animateAlongRoute = async (marker, route) => {
    for (let i = 0; i < route.length; i++) {
      const point = route[i]
      marker.setLatLng([point.lat, point.lng])
      setCurrentStep(i)
      await sleep(200)
    }
  }

  const getWarehouseCoords = async (city) => {
    try {
      const response = await fetch('http://localhost:8001/api/warehouses')
      const warehouses = await response.json()
      const warehouse = warehouses.find(w => w.city === city)
      if (warehouse) {
        return warehouse.location
      }
    } catch (error) {
      console.error('Error fetching warehouse:', error)
    }
    
    // Fallback to city center
    const cityCoords = await getCoordinates(city, '')
    return { lat: cityCoords.lat + 0.02, lng: cityCoords.lng + 0.02 }
  }

  const fetchRouteOSRM = async (start, end) => {
    try {
      const url = `http://router.project-osrm.org/route/v1/driving/${start.lng},${start.lat};${end.lng},${end.lat}?overview=full&geometries=geojson`
      const response = await fetch(url)
      
      if (response.ok) {
        const data = await response.json()
        if (data.routes && data.routes[0]) {
          const coords = data.routes[0].geometry.coordinates
          return coords.map(c => ({ lat: c[1], lng: c[0] }))
        }
      }
    } catch (error) {
      console.error('OSRM routing failed:', error)
    }
    
    // Fallback to simple route
    return generateSimpleRoute(start, end, end).slice(0, 15)
  }

  const drawSingleRoute = (route, mapInstance, color) => {
    if (route.length > 0) {
      window.L.polyline(route.map(p => [p.lat, p.lng]), { 
        color, 
        weight: 4, 
        opacity: 0.7,
        dashArray: color === 'red' ? '10, 5' : null
      }).addTo(mapInstance)
    }
  }

  const fetchRoute = async (start, pickup, delivery) => {
    try {
      console.log('Fetching route with:', { start, pickup, delivery })
      
      const response = await fetch('http://localhost:8001/api/routing/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_location: start,
          waypoints: [pickup, delivery],
          vehicle_type: driver?.vehicle_type || 'car'
        })
      })
      
      if (!response.ok) {
        console.error('Routing API failed, using fallback')
        return generateSimpleRoute(start, pickup, delivery)
      }
      
      const data = await response.json()
      console.log('Route data received:', data)
      return data.route || generateSimpleRoute(start, pickup, delivery)
    } catch (error) {
      console.error('Routing error:', error)
      return generateSimpleRoute(start, pickup, delivery)
    }
  }

  const generateSimpleRoute = (start, pickup, delivery) => {
    const route = []
    
    // Driver to pickup (10 points)
    for (let i = 0; i <= 10; i++) {
      const ratio = i / 10
      route.push({
        lat: start.lat + (pickup.lat - start.lat) * ratio,
        lng: start.lng + (pickup.lng - start.lng) * ratio,
        type: 'to_pickup'
      })
    }
    
    // Pickup to delivery (15 points)
    for (let i = 1; i <= 15; i++) {
      const ratio = i / 15
      route.push({
        lat: pickup.lat + (delivery.lat - pickup.lat) * ratio,
        lng: pickup.lng + (delivery.lng - pickup.lng) * ratio,
        type: 'to_delivery'
      })
    }
    
    return route
  }

  const drawRoute = (routeData, mapInstance) => {
    const toPickup = routeData.filter(p => p.type === 'to_pickup').map(p => [p.lat, p.lng])
    const toDelivery = routeData.filter(p => p.type === 'to_delivery').map(p => [p.lat, p.lng])

    if (toPickup.length > 0) {
      window.L.polyline(toPickup, { color: 'blue', weight: 4, opacity: 0.6, dashArray: '10, 10' })
        .addTo(mapInstance)
    }

    if (toDelivery.length > 0) {
      window.L.polyline(toDelivery, { color: 'green', weight: 4, opacity: 0.6 })
        .addTo(mapInstance)
    }
  }

  const animateDelivery = async (marker, routeData, pickup, delivery) => {
    const toPickupRoute = routeData.filter(p => p.type === 'to_pickup')
    const toDeliveryRoute = routeData.filter(p => p.type === 'to_delivery')

    // Phase 1: Moving to pickup
    addEvent('Driver heading to pickup location', 'info')
    await updateOrderStatus('in_transit')
    
    for (let i = 0; i < toPickupRoute.length; i++) {
      const point = toPickupRoute[i]
      marker.setLatLng([point.lat, point.lng])
      setCurrentStep(i)
      await sleep(300)
    }

    // Phase 2: At pickup
    addEvent('Driver arrived at pickup location', 'success')
    await sleep(2000)
    addEvent('Package picked up', 'success')
    await updateOrderStatus('picked_up')
    await sleep(2000)

    // Phase 3: Moving to delivery
    addEvent('Driver heading to delivery location', 'info')
    await updateOrderStatus('out_for_delivery')
    
    for (let i = 0; i < toDeliveryRoute.length; i++) {
      const point = toDeliveryRoute[i]
      marker.setLatLng([point.lat, point.lng])
      setCurrentStep(toPickupRoute.length + i)
      await sleep(300)
    }

    // Phase 4: Delivered
    addEvent('Package delivered successfully!', 'success')
    await updateOrderStatus('delivered')
    setSimulationStatus('completed')
    
    // Refresh order data
    setTimeout(() => fetchOrderData(), 1000)
  }

  const updateOrderStatus = async (status) => {
    try {
      const auth = JSON.parse(localStorage.getItem('auth') || '{}')
      await fetch(`http://localhost:8001/api/orders/${orderId}/status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${auth.access_token}`
        },
        body: JSON.stringify({ order_id: orderId, status, notes: 'Simulation update' })
      })
      
      // Update local order state
      setOrder(prev => ({ ...prev, status }))
    } catch (error) {
      console.error('Error updating status:', error)
    }
  }



  const createCustomIcon = (emoji, color) => {
    return window.L.divIcon({
      html: `<div style="font-size: 24px; text-align: center;">${emoji}</div>`,
      className: 'custom-marker',
      iconSize: [30, 30],
      iconAnchor: [15, 15]
    })
  }

  const getVehicleIcon = (type) => {
    const icons = { bike: '🚴', scooter: '🛵', car: '🚗', van: '🚐', truck: '🚚' }
    return icons[type] || '🚗'
  }

  const addEvent = (message, type) => {
    setEvents(prev => [...prev, {
      message,
      type,
      timestamp: new Date().toLocaleTimeString()
    }])
  }

  const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

  const getStatusColor = (status) => {
    const colors = {
      'pending_assignment': 'gray',
      'assigned': 'blue',
      'in_transit': 'yellow',
      'picked_up': 'orange',
      'out_for_delivery': 'purple',
      'delivered': 'green'
    }
    return colors[status] || 'gray'
  }

  if (!order) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">🎬 Delivery Simulation</h1>
            <p className="text-sm opacity-90">Order: {order.tracking_number}</p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-gray-100"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      <div className="flex-1 flex">
        {/* Map */}
        <div className="flex-1 relative">
          <div ref={mapRef} className="w-full h-full" />
          
          {/* Simulation Controls */}
          <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 z-[1000]">
            <div className="flex items-center gap-3 mb-3">
              <Package className="w-6 h-6 text-blue-600" />
              <div>
                <div className="font-semibold">{order.package_description}</div>
                <div className="text-sm text-gray-600">{order.weight}kg</div>
              </div>
            </div>
            
            {simulationStatus === 'initializing' && (
              <button
                onClick={startSimulation}
                className="w-full px-4 py-2 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-lg hover:from-green-600 hover:to-blue-600 font-semibold"
              >
                ▶️ Start Simulation
              </button>
            )}
            
            {simulationStatus === 'running' && (
              <div className="text-center">
                <div className="animate-pulse text-blue-600 font-semibold">🚚 Simulation Running...</div>
                <div className="text-xs text-gray-600 mt-1">Step {currentStep}/{route.length}</div>
              </div>
            )}
            
            {simulationStatus === 'completed' && (
              <div className="text-center text-green-600 font-semibold">
                ✅ Delivery Completed!
              </div>
            )}
          </div>

          {/* Weather & Traffic */}
          <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-4 z-[1000] space-y-3">
            {weather && (
              <div className="flex items-center gap-2">
                <Cloud className="w-5 h-5 text-blue-500" />
                <div>
                  <div className="text-sm font-semibold">{weather.condition}</div>
                  <div className="text-xs text-gray-600">{weather.temperature}°C</div>
                </div>
              </div>
            )}
            
            <div className="flex items-center gap-2">
              <AlertTriangle className={`w-5 h-5 ${traffic === 'heavy' ? 'text-red-500' : traffic === 'moderate' ? 'text-yellow-500' : 'text-green-500'}`} />
              <div>
                <div className="text-sm font-semibold capitalize">{traffic} Traffic</div>
                <div className="text-xs text-gray-600">Current conditions</div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="w-96 bg-gray-50 border-l overflow-y-auto">
          {/* Status */}
          <div className="p-4 bg-white border-b">
            <div className="flex items-center gap-2 mb-2">
              <div className={`w-3 h-3 rounded-full bg-${getStatusColor(order.status)}-500 animate-pulse`} />
              <span className="font-semibold capitalize">{order.status.replace(/_/g, ' ')}</span>
            </div>
            <div className="text-sm text-gray-600">
              {order.pickup_city} → {order.delivery_city}
            </div>
          </div>

          {/* Driver Info */}
          {driver && (
            <div className="p-4 bg-white border-b">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-2xl">
                  {getVehicleIcon(driver.vehicle_type)}
                </div>
                <div>
                  <div className="font-semibold">{driver.name}</div>
                  <div className="text-sm text-gray-600 capitalize">{driver.vehicle_type}</div>
                  <div className="text-xs text-yellow-600">⭐ {driver.rating}/5.0</div>
                </div>
              </div>
            </div>
          )}

          {/* Events Timeline */}
          <div className="p-4">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Live Events
            </h3>
            <div className="space-y-2">
              {events.map((event, idx) => (
                <div key={idx} className={`p-3 rounded-lg ${
                  event.type === 'success' ? 'bg-green-50 border border-green-200' :
                  event.type === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
                  'bg-blue-50 border border-blue-200'
                }`}>
                  <div className="flex items-start gap-2">
                    {event.type === 'success' ? <CheckCircle className="w-4 h-4 text-green-600 mt-0.5" /> :
                     event.type === 'warning' ? <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5" /> :
                     <Navigation className="w-4 h-4 text-blue-600 mt-0.5" />}
                    <div className="flex-1">
                      <div className="text-sm font-medium">{event.message}</div>
                      <div className="text-xs text-gray-500">{event.timestamp}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Route Details */}
          <div className="p-4 bg-white border-t">
            <h3 className="font-semibold mb-2">Route Information</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Distance:</span>
                <span className="font-medium">{(route.length * 0.5).toFixed(1)} km</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Estimated Time:</span>
                <span className="font-medium">{Math.ceil(route.length * 0.3)} min</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Service Type:</span>
                <span className="font-medium capitalize">{order.service_type}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
