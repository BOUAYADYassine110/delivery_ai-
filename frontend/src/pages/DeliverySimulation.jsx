import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { MapPin, Package, Truck, Clock, Navigation, Cloud, AlertTriangle, CheckCircle, ArrowLeft, Play, Pause, RotateCcw, Zap, TrendingUp } from 'lucide-react'

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
  const [routeMetrics, setRouteMetrics] = useState({ distance: 0, duration: 0 })
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
    if (!order || !map) return

    // If no driver assigned, assign one first
    if (!order.assigned_driver || !driver) {
      setSimulationStatus('assigning')
      addEvent('Assigning driver to order...', 'info')
      
      try {
        const auth = JSON.parse(localStorage.getItem('auth') || '{}')
        const response = await fetch(`http://localhost:8001/api/orders/${orderId}/assign-driver`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${auth.access_token}` }
        })
        
        const data = await response.json()
        
        if (data.error) {
          addEvent(`Error: ${data.error}`, 'warning')
          setSimulationStatus('initializing')
          return
        }
        
        addEvent(`Driver ${data.driver} assigned!`, 'success')
        
        // Refresh order data
        await fetchOrderData()
        await sleep(1000)
      } catch (error) {
        console.error('Error assigning driver:', error)
        addEvent('Failed to assign driver', 'warning')
        setSimulationStatus('initializing')
        return
      }
    }

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

    let totalDistance = 0
    let totalDuration = 0

    // Phase 1: Warehouse to Pickup (use OSRM)
    addEvent(`Driver leaving ${order.pickup_city} warehouse`, 'info')
    await updateOrderStatus('en_route_to_pickup')
    const toPickupRoute = await fetchRouteOSRM(originWarehouse, pickupCoords)
    drawSingleRoute(toPickupRoute.coordinates, map, 'blue')
    await animateAlongRoute(dMarker, toPickupRoute.coordinates)
    totalDistance += parseFloat(toPickupRoute.distance) || 0
    totalDuration += toPickupRoute.duration || 0

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
    drawSingleRoute(backToWarehouseRoute.coordinates, map, 'orange')
    await animateAlongRoute(dMarker, backToWarehouseRoute.coordinates)
    totalDistance += parseFloat(backToWarehouseRoute.distance) || 0
    totalDuration += backToWarehouseRoute.duration || 0

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
    drawSingleRoute(interCityRoute.coordinates, map, 'red')
    await animateAlongRoute(truckMarker, interCityRoute.coordinates)
    totalDistance += parseFloat(interCityRoute.distance) || 0
    totalDuration += interCityRoute.duration || 0

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
      setRouteMetrics({ distance: totalDistance, duration: totalDuration })
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
      drawSingleRoute(finalRoute.coordinates, map, 'green')
      await animateAlongRoute(finalDriver, finalRoute.coordinates)
      totalDistance += parseFloat(finalRoute.distance) || 0
      totalDuration += finalRoute.duration || 0

      addEvent('Package delivered to customer door!', 'success')
      await updateOrderStatus('delivered')
      setSimulationStatus('completed')
      setRouteMetrics({ distance: totalDistance, duration: totalDuration })
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

    // Get separate routes for each segment
    const toPickupRoute = await fetchRouteOSRM(driverStart, pickupCoords)
    const toDeliveryRoute = await fetchRouteOSRM(pickupCoords, deliveryCoords)
    
    // Draw both routes
    drawSingleRoute(toPickupRoute.coordinates, map, 'blue')
    drawSingleRoute(toDeliveryRoute.coordinates, map, 'green')
    
    // Store combined metrics
    const totalDistance = (parseFloat(toPickupRoute.distance) || 0) + (parseFloat(toDeliveryRoute.distance) || 0)
    const totalDuration = (toPickupRoute.duration || 0) + (toDeliveryRoute.duration || 0)
    setRouteMetrics({ distance: totalDistance, duration: totalDuration })
    setRoute([...toPickupRoute.coordinates, ...toDeliveryRoute.coordinates])
    
    await animateIntraCityDelivery(dMarker, toPickupRoute.coordinates, toDeliveryRoute.coordinates)
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
          const route = data.routes[0]
          const coords = route.geometry.coordinates
          const distance = (route.distance / 1000).toFixed(1) // km
          const duration = Math.round(route.duration / 60) // minutes
          
          return {
            coordinates: coords.map(c => ({ lat: c[1], lng: c[0] })),
            distance,
            duration
          }
        }
      }
    } catch (error) {
      console.error('OSRM routing failed:', error)
    }
    
    // Fallback to simple route
    const simpleRoute = generateSimpleRoute(start, end, end).slice(0, 15)
    return {
      coordinates: simpleRoute,
      distance: 0,
      duration: 0
    }
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
        return { route: generateSimpleRoute(start, pickup, delivery), distance: 0, duration: 0 }
      }
      
      const data = await response.json()
      console.log('Route data received:', data)
      
      // Store metrics
      if (data.distance && data.duration) {
        setRouteMetrics({ distance: data.distance, duration: data.duration })
      }
      
      return { route: data.route || generateSimpleRoute(start, pickup, delivery), distance: data.distance || 0, duration: data.duration || 0 }
    } catch (error) {
      console.error('Routing error:', error)
      return { route: generateSimpleRoute(start, pickup, delivery), distance: 0, duration: 0 }
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

  const animateIntraCityDelivery = async (marker, toPickupRoute, toDeliveryRoute) => {
    // Phase 1: Moving to pickup
    addEvent('Driver heading to pickup location', 'info')
    await updateOrderStatus('in_transit')
    
    for (let i = 0; i < toPickupRoute.length; i++) {
      const point = toPickupRoute[i]
      marker.setLatLng([point.lat, point.lng])
      setCurrentStep(i)
      await sleep(200)
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
      await sleep(200)
    }

    // Phase 4: Delivered
    addEvent('Package delivered successfully!', 'success')
    await updateOrderStatus('delivered')
    setSimulationStatus('completed')
    
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
    const colors = {
      blue: '#3B82F6',
      green: '#10B981',
      orange: '#F59E0B',
      purple: '#8B5CF6',
      red: '#EF4444'
    }
    
    return window.L.divIcon({
      html: `<div style="
        background: ${colors[color] || color};
        width: 32px;
        height: 32px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <span style="transform: rotate(45deg); font-size: 18px;">${emoji}</span>
      </div>`,
      className: '',
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32]
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
    <div className="h-screen flex flex-col bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Modern Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </button>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <Package className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">Live Delivery Simulation</h1>
                  <p className="text-sm text-gray-500">Tracking: {order.tracking_number}</p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {simulationStatus === 'initializing' && (
                <button
                  onClick={startSimulation}
                  className="px-6 py-2.5 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl hover:from-green-600 hover:to-emerald-700 font-semibold shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
                >
                  <Play className="w-4 h-4" />
                  Start Simulation
                </button>
              )}
              {simulationStatus === 'running' && (
                <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-xl border border-blue-200">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                  <span className="text-sm font-medium text-blue-700">Simulation Running</span>
                </div>
              )}
              {simulationStatus === 'completed' && (
                <div className="flex items-center gap-2 px-4 py-2 bg-green-50 rounded-xl border border-green-200">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span className="text-sm font-medium text-green-700">Completed</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Map Container */}
        <div className="flex-1 relative">
          <div ref={mapRef} className="w-full h-full" />
          
          {/* Floating Info Cards */}
          <div className="absolute top-6 left-6 right-6 flex justify-between items-start z-[1000] pointer-events-none">
            {/* Package Info Card */}
            <div className="bg-white rounded-2xl shadow-xl p-4 max-w-xs pointer-events-auto">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center">
                  <Package className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">{order.package_description}</div>
                  <div className="text-sm text-gray-500">{order.weight}kg • {order.service_type}</div>
                </div>
              </div>
              <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                <span className="text-xs text-gray-500">Route</span>
                <span className="text-sm font-medium text-gray-900">{order.pickup_city} → {order.delivery_city}</span>
              </div>
            </div>

            {/* Weather & Traffic Card */}
            <div className="bg-white rounded-2xl shadow-xl p-4 space-y-3 pointer-events-auto">
              {weather && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                    <Cloud className="w-5 h-5 text-blue-500" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-gray-900">{weather.condition}</div>
                    <div className="text-xs text-gray-500">{weather.temperature}°C</div>
                  </div>
                </div>
              )}
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  traffic === 'heavy' ? 'bg-red-50' : traffic === 'moderate' ? 'bg-yellow-50' : 'bg-green-50'
                }`}>
                  <AlertTriangle className={`w-5 h-5 ${
                    traffic === 'heavy' ? 'text-red-500' : traffic === 'moderate' ? 'text-yellow-500' : 'text-green-500'
                  }`} />
                </div>
                <div>
                  <div className="text-sm font-semibold text-gray-900 capitalize">{traffic} Traffic</div>
                  <div className="text-xs text-gray-500">Current conditions</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Modern Sidebar */}
        <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
          {/* Status Header */}
          <div className="p-6 border-b border-gray-200 bg-gradient-to-br from-gray-50 to-white">
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-3 h-3 rounded-full animate-pulse ${
                order.status === 'delivered' ? 'bg-green-500' :
                order.status === 'in_transit' ? 'bg-blue-500' :
                order.status === 'picked_up' ? 'bg-purple-500' :
                'bg-yellow-500'
              }`} />
              <span className="font-semibold text-gray-900 capitalize">{order.status.replace(/_/g, ' ')}</span>
            </div>
            <div className="text-sm text-gray-600">
              {order.pickup_city} → {order.delivery_city}
            </div>
          </div>

          {/* Driver Info */}
          {driver && (
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center text-2xl shadow-lg">
                  {getVehicleIcon(driver.vehicle_type)}
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">{driver.name}</div>
                  <div className="text-sm text-gray-500 capitalize">{driver.vehicle_type}</div>
                  <div className="flex items-center gap-1 mt-1">
                    <span className="text-yellow-500">⭐</span>
                    <span className="text-sm font-medium text-gray-700">{driver.rating}/5.0</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Route Metrics */}
          <div className="p-6 border-b border-gray-200 bg-gradient-to-br from-blue-50 to-indigo-50">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              Route Metrics
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-xl p-3 shadow-sm">
                <div className="text-xs text-gray-500 mb-1">Distance</div>
                <div className="text-lg font-bold text-gray-900">
                  {routeMetrics.distance > 0 ? `${routeMetrics.distance} km` : '--'}
                </div>
              </div>
              <div className="bg-white rounded-xl p-3 shadow-sm">
                <div className="text-xs text-gray-500 mb-1">Duration</div>
                <div className="text-lg font-bold text-gray-900">
                  {routeMetrics.duration > 0 ? `${routeMetrics.duration} min` : '--'}
                </div>
              </div>
              <div className="bg-white rounded-xl p-3 shadow-sm">
                <div className="text-xs text-gray-500 mb-1">Service</div>
                <div className="text-sm font-semibold text-gray-900 capitalize flex items-center gap-1">
                  {order.service_type === 'express' && <Zap className="w-3 h-3 text-yellow-500" />}
                  {order.service_type}
                </div>
              </div>
              <div className="bg-white rounded-xl p-3 shadow-sm">
                <div className="text-xs text-gray-500 mb-1">Type</div>
                <div className="text-sm font-semibold text-gray-900">
                  {order.is_inter_city ? 'Inter-City' : 'Intra-City'}
                </div>
              </div>
            </div>
          </div>

          {/* Events Timeline */}
          <div className="flex-1 overflow-y-auto p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5 text-gray-600" />
              Live Events
            </h3>
            <div className="space-y-3">
              {events.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <Navigation className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No events yet</p>
                </div>
              ) : (
                events.map((event, idx) => (
                  <div key={idx} className={`relative pl-6 pb-3 ${
                    idx !== events.length - 1 ? 'border-l-2 border-gray-200' : ''
                  }`}>
                    <div className={`absolute left-0 top-0 -ml-1.5 w-3 h-3 rounded-full ${
                      event.type === 'success' ? 'bg-green-500' :
                      event.type === 'warning' ? 'bg-yellow-500' :
                      'bg-blue-500'
                    }`} />
                    <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-100">
                      <div className="flex items-start gap-2">
                        {event.type === 'success' ? <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" /> :
                         event.type === 'warning' ? <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 flex-shrink-0" /> :
                         <Navigation className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />}
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900">{event.message}</div>
                          <div className="text-xs text-gray-500 mt-1">{event.timestamp}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
