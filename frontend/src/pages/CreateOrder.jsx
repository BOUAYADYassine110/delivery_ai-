import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Package, MapPin, User, Phone, Weight, Box, Truck, Warehouse, DollarSign } from 'lucide-react'
import MapPicker from '../components/MapPicker'
import AIProcessingModal from '../components/AIProcessingModal'

export default function CreateOrder() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [showAIModal, setShowAIModal] = useState(false)
  const [showPickupMap, setShowPickupMap] = useState(false)
  const [showDeliveryMap, setShowDeliveryMap] = useState(false)
  const [priceEstimate, setPriceEstimate] = useState(null)
  const [formData, setFormData] = useState({
    sender_name: '',
    sender_phone: '',
    pickup_address: '',
    pickup_city: 'Casablanca',
    pickup_coordinates: null,
    receiver_name: '',
    receiver_phone: '',
    delivery_address: '',
    delivery_city: 'Casablanca',
    delivery_coordinates: null,
    weight: '',
    length: '',
    width: '',
    height: '',
    package_description: '',
    service_type: 'standard',
    pickup_option: 'door_pickup',
    delivery_option: 'door_delivery',
    fragile: false,
    insurance_value: 0
  })

  const cities = ['Casablanca', 'Rabat', 'Marrakech', 'El Jadida', 'Salé', 'Agadir']
  const isInterCity = formData.pickup_city !== formData.delivery_city

  useEffect(() => {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)

    const script = document.createElement('script')
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    document.body.appendChild(script)

    return () => {
      if (document.head.contains(link)) document.head.removeChild(link)
      if (document.body.contains(script)) document.body.removeChild(script)
    }
  }, [])

  // Calculate price estimate
  useEffect(() => {
    if (formData.weight && formData.length && formData.width && formData.height) {
      calculatePrice()
    }
  }, [formData.pickup_city, formData.delivery_city, formData.weight, formData.service_type, 
      formData.pickup_option, formData.delivery_option, formData.fragile, formData.insurance_value])

  const calculatePrice = async () => {
    const basePrice = isInterCity ? 80 : 25
    const weight = parseFloat(formData.weight) || 1
    const weightCost = isInterCity ? weight * 8 : weight * 3
    
    let warehouseFee = 0
    if (isInterCity) {
      if (formData.pickup_option === 'warehouse_dropoff') warehouseFee += 15
      if (formData.delivery_option === 'warehouse_pickup') warehouseFee += 15
    }
    
    const insuranceFee = parseFloat(formData.insurance_value) * 0.02
    const fragileFee = formData.fragile ? 25 : 0
    const serviceMultiplier = formData.service_type === 'express' ? 1.5 : 1.0
    
    const total = (basePrice + weightCost + warehouseFee + insuranceFee + fragileFee) * serviceMultiplier
    
    setPriceEstimate({
      base: basePrice,
      weight: weightCost,
      warehouse: warehouseFee,
      insurance: insuranceFee,
      fragile: fragileFee,
      multiplier: serviceMultiplier,
      total: Math.round(total * 100) / 100
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setShowAIModal(true)

    try {
      const auth = JSON.parse(localStorage.getItem('auth') || '{}')
      const token = auth.access_token

      if (!token) {
        setShowAIModal(false)
        alert('Please login first')
        navigate('/login')
        return
      }

      const endpoint = isInterCity ? '/api/inter-city/orders' : '/api/orders'
      
      const orderData = isInterCity ? {
        pickup_address: formData.pickup_address,
        delivery_address: formData.delivery_address,
        pickup_city: formData.pickup_city,
        delivery_city: formData.delivery_city,
        pickup_coordinates: formData.pickup_coordinates,
        delivery_coordinates: formData.delivery_coordinates,
        sender_name: formData.sender_name,
        sender_phone: formData.sender_phone,
        receiver_name: formData.receiver_name,
        receiver_phone: formData.receiver_phone,
        weight: parseFloat(formData.weight),
        dimensions: {
          length: parseFloat(formData.length),
          width: parseFloat(formData.width),
          height: parseFloat(formData.height)
        },
        service_type: formData.service_type,
        pickup_option: formData.pickup_option,
        delivery_option: formData.delivery_option,
        package_description: formData.package_description,
        fragile: formData.fragile,
        insurance_value: parseFloat(formData.insurance_value) || 0
      } : {
        pickup_address: formData.pickup_address,
        delivery_address: formData.delivery_address,
        pickup_city: formData.pickup_city,
        delivery_city: formData.delivery_city,
        pickup_coordinates: formData.pickup_coordinates,
        delivery_coordinates: formData.delivery_coordinates,
        sender_name: formData.sender_name,
        sender_phone: formData.sender_phone,
        receiver_name: formData.receiver_name,
        receiver_phone: formData.receiver_phone,
        weight: parseFloat(formData.weight),
        dimensions: {
          length: parseFloat(formData.length),
          width: parseFloat(formData.width),
          height: parseFloat(formData.height)
        },
        service_type: formData.service_type,
        package_description: formData.package_description,
        delivery_type: 'door_to_door'
      }

      const [response] = await Promise.all([
        fetch(`http://localhost:8001${endpoint}`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(orderData)
        }),
        new Promise(resolve => setTimeout(resolve, 6000))
      ])

      setShowAIModal(false)

      if (response.status === 401) {
        localStorage.removeItem('auth')
        alert('Session expired. Please login again')
        navigate('/login')
        return
      }

      if (response.ok) {
        const data = await response.json()
        alert(`Order created! Tracking: ${data.tracking_number}\nTotal Cost: ${data.total_cost} MAD`)
        navigate('/dashboard')
      } else {
        alert('Failed to create order')
      }
    } catch (error) {
      setShowAIModal(false)
      alert('Error: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto">
      <AIProcessingModal 
        isOpen={showAIModal} 
        onClose={() => setShowAIModal(false)}
        orderData={{
          pickup_city: formData.pickup_city,
          delivery_city: formData.delivery_city,
          service_type: formData.service_type
        }}
      />

      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
            <Package className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Create Order</h1>
        </div>
        {isInterCity && (
          <div className="flex items-center gap-2 mt-4 px-4 py-3 bg-gradient-to-r from-orange-100 to-red-100 text-orange-900 rounded-lg w-fit border border-orange-300">
            <Truck className="w-5 h-5" />
            <span className="font-semibold">Inter-City Delivery - Warehouse Processing Required</span>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Sender & Receiver */}
        <div className="grid md:grid-cols-2 gap-6">
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <User className="w-5 h-5 text-blue-600" />
              <h3 className="font-semibold text-lg">Sender</h3>
            </div>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Full Name"
                value={formData.sender_name}
                onChange={(e) => setFormData({...formData, sender_name: e.target.value})}
                className="input"
                required
              />
              <input
                type="tel"
                placeholder="Phone Number"
                value={formData.sender_phone}
                onChange={(e) => setFormData({...formData, sender_phone: e.target.value})}
                className="input"
                required
              />
              <select
                value={formData.pickup_city}
                onChange={(e) => setFormData({...formData, pickup_city: e.target.value})}
                className="input"
                required
              >
                {cities.map(city => (
                  <option key={city} value={city}>{city}</option>
                ))}
              </select>
              <textarea
                placeholder="Pickup Address"
                value={formData.pickup_address}
                onChange={(e) => setFormData({...formData, pickup_address: e.target.value})}
                className="input"
                rows="3"
                required
              />
              <button
                type="button"
                onClick={() => setShowPickupMap(!showPickupMap)}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1 mt-2"
              >
                <MapPin className="w-4 h-4" />
                {showPickupMap ? 'Hide Map' : 'Pick on Map'}
              </button>
              {showPickupMap && (
                <div className="mt-3">
                  <MapPicker
                    onLocationSelect={(loc) => setFormData({...formData, pickup_address: loc.address, pickup_coordinates: {lat: loc.lat, lng: loc.lng}})}
                    initialPosition={[33.5731, -7.5898]}
                  />
                </div>
              )}
              {formData.pickup_coordinates && (
                <div className="text-xs text-green-600 mt-1">
                  📍 Location saved: {formData.pickup_coordinates.lat.toFixed(4)}, {formData.pickup_coordinates.lng.toFixed(4)}
                </div>
              )}
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center gap-2 mb-4">
              <MapPin className="w-5 h-5 text-green-600" />
              <h3 className="font-semibold text-lg">Receiver</h3>
            </div>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Full Name"
                value={formData.receiver_name}
                onChange={(e) => setFormData({...formData, receiver_name: e.target.value})}
                className="input"
                required
              />
              <input
                type="tel"
                placeholder="Phone Number"
                value={formData.receiver_phone}
                onChange={(e) => setFormData({...formData, receiver_phone: e.target.value})}
                className="input"
                required
              />
              <select
                value={formData.delivery_city}
                onChange={(e) => setFormData({...formData, delivery_city: e.target.value})}
                className="input"
                required
              >
                {cities.map(city => (
                  <option key={city} value={city}>{city}</option>
                ))}
              </select>
              <textarea
                placeholder="Delivery Address"
                value={formData.delivery_address}
                onChange={(e) => setFormData({...formData, delivery_address: e.target.value})}
                className="input"
                rows="3"
                required
              />
              <button
                type="button"
                onClick={() => setShowDeliveryMap(!showDeliveryMap)}
                className="text-sm text-green-600 hover:text-green-700 font-medium flex items-center gap-1 mt-2"
              >
                <MapPin className="w-4 h-4" />
                {showDeliveryMap ? 'Hide Map' : 'Pick on Map'}
              </button>
              {showDeliveryMap && (
                <div className="mt-3">
                  <MapPicker
                    onLocationSelect={(loc) => setFormData({...formData, delivery_address: loc.address, delivery_coordinates: {lat: loc.lat, lng: loc.lng}})}
                    initialPosition={[33.5731, -7.5898]}
                  />
                </div>
              )}
              {formData.delivery_coordinates && (
                <div className="text-xs text-green-600 mt-1">
                  📍 Location saved: {formData.delivery_coordinates.lat.toFixed(4)}, {formData.delivery_coordinates.lng.toFixed(4)}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Inter-City Options */}
        {isInterCity && (
          <div className="card p-6 bg-gradient-to-br from-orange-50 to-red-50 border-2 border-orange-200">
            <div className="flex items-center gap-2 mb-4">
              <Warehouse className="w-5 h-5 text-orange-600" />
              <h3 className="font-semibold text-lg">Delivery Options</h3>
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Pickup Method</label>
                <div className="space-y-2">
                  <label className={`flex items-center p-3 border-2 rounded-lg cursor-pointer ${
                    formData.pickup_option === 'door_pickup' ? 'border-orange-600 bg-orange-50' : 'border-gray-300'
                  }`}>
                    <input
                      type="radio"
                      name="pickup_option"
                      value="door_pickup"
                      checked={formData.pickup_option === 'door_pickup'}
                      onChange={(e) => setFormData({...formData, pickup_option: e.target.value})}
                      className="mr-3"
                    />
                    <div>
                      <div className="font-medium">Door Pickup</div>
                      <div className="text-sm text-gray-600">Driver collects from address</div>
                    </div>
                  </label>
                  <label className={`flex items-center p-3 border-2 rounded-lg cursor-pointer ${
                    formData.pickup_option === 'warehouse_dropoff' ? 'border-orange-600 bg-orange-50' : 'border-gray-300'
                  }`}>
                    <input
                      type="radio"
                      name="pickup_option"
                      value="warehouse_dropoff"
                      checked={formData.pickup_option === 'warehouse_dropoff'}
                      onChange={(e) => setFormData({...formData, pickup_option: e.target.value})}
                      className="mr-3"
                    />
                    <div>
                      <div className="font-medium">Warehouse Dropoff (+15 MAD)</div>
                      <div className="text-sm text-gray-600">You drop at warehouse</div>
                    </div>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Delivery Method</label>
                <div className="space-y-2">
                  <label className={`flex items-center p-3 border-2 rounded-lg cursor-pointer ${
                    formData.delivery_option === 'door_delivery' ? 'border-orange-600 bg-orange-50' : 'border-gray-300'
                  }`}>
                    <input
                      type="radio"
                      name="delivery_option"
                      value="door_delivery"
                      checked={formData.delivery_option === 'door_delivery'}
                      onChange={(e) => setFormData({...formData, delivery_option: e.target.value})}
                      className="mr-3"
                    />
                    <div>
                      <div className="font-medium">Door Delivery</div>
                      <div className="text-sm text-gray-600">Driver delivers to address</div>
                    </div>
                  </label>
                  <label className={`flex items-center p-3 border-2 rounded-lg cursor-pointer ${
                    formData.delivery_option === 'warehouse_pickup' ? 'border-orange-600 bg-orange-50' : 'border-gray-300'
                  }`}>
                    <input
                      type="radio"
                      name="delivery_option"
                      value="warehouse_pickup"
                      checked={formData.delivery_option === 'warehouse_pickup'}
                      onChange={(e) => setFormData({...formData, delivery_option: e.target.value})}
                      className="mr-3"
                    />
                    <div>
                      <div className="font-medium">Warehouse Pickup (+15 MAD)</div>
                      <div className="text-sm text-gray-600">Receiver collects from warehouse</div>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Package Details */}
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Box className="w-5 h-5 text-purple-600" />
            <h3 className="font-semibold text-lg">Package Details</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Weight (kg)</label>
              <input
                type="number"
                step="0.1"
                placeholder="5.0"
                value={formData.weight}
                onChange={(e) => setFormData({...formData, weight: e.target.value})}
                className="input"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Length (cm)</label>
              <input
                type="number"
                placeholder="30"
                value={formData.length}
                onChange={(e) => setFormData({...formData, length: e.target.value})}
                className="input"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Width (cm)</label>
              <input
                type="number"
                placeholder="20"
                value={formData.width}
                onChange={(e) => setFormData({...formData, width: e.target.value})}
                className="input"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Height (cm)</label>
              <input
                type="number"
                placeholder="10"
                value={formData.height}
                onChange={(e) => setFormData({...formData, height: e.target.value})}
                className="input"
                required
              />
            </div>
          </div>
          <input
            type="text"
            placeholder="Package Description (e.g., Electronics, Documents)"
            value={formData.package_description}
            onChange={(e) => setFormData({...formData, package_description: e.target.value})}
            className="input mb-4"
            required
          />
          
          {isInterCity && (
            <div className="grid md:grid-cols-2 gap-4">
              <label className="flex items-center p-3 border-2 rounded-lg cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.fragile}
                  onChange={(e) => setFormData({...formData, fragile: e.target.checked})}
                  className="mr-3"
                />
                <div>
                  <div className="font-medium">Fragile Item (+25 MAD)</div>
                  <div className="text-sm text-gray-600">Special handling required</div>
                </div>
              </label>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Insurance Value (MAD)</label>
                <input
                  type="number"
                  placeholder="0"
                  value={formData.insurance_value}
                  onChange={(e) => setFormData({...formData, insurance_value: e.target.value})}
                  className="input"
                />
                <div className="text-xs text-gray-500 mt-1">2% of declared value</div>
              </div>
            </div>
          )}
        </div>

        {/* Service Type */}
        <div className="card p-6">
          <h3 className="font-semibold text-lg mb-4">Service Type</h3>
          <div className="grid grid-cols-2 gap-4">
            <label className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
              formData.service_type === 'standard' 
                ? 'border-blue-600 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}>
              <input
                type="radio"
                name="service_type"
                value="standard"
                checked={formData.service_type === 'standard'}
                onChange={(e) => setFormData({...formData, service_type: e.target.value})}
                className="sr-only"
              />
              <div className="text-center">
                <div className="font-semibold">Standard</div>
                <div className="text-sm text-gray-600">{isInterCity ? '2-3 days' : '1-2 days'}</div>
              </div>
            </label>
            <label className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
              formData.service_type === 'express' 
                ? 'border-blue-600 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
            }`}>
              <input
                type="radio"
                name="service_type"
                value="express"
                checked={formData.service_type === 'express'}
                onChange={(e) => setFormData({...formData, service_type: e.target.value})}
                className="sr-only"
              />
              <div className="text-center">
                <div className="font-semibold">Express</div>
                <div className="text-sm text-gray-600">{isInterCity ? 'Next day' : 'Same day'}</div>
                <div className="text-xs text-orange-600 font-medium mt-1">
                  1.5x price
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Price Estimate */}
        {priceEstimate && (
          <div className="card p-6 bg-gradient-to-br from-green-50 to-blue-50 border-2 border-green-200">
            <div className="flex items-center gap-2 mb-4">
              <DollarSign className="w-5 h-5 text-green-600" />
              <h3 className="font-semibold text-lg">Price Estimate</h3>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Base Price:</span>
                <span className="font-medium">{priceEstimate.base} MAD</span>
              </div>
              <div className="flex justify-between">
                <span>Weight Cost:</span>
                <span className="font-medium">{priceEstimate.weight.toFixed(2)} MAD</span>
              </div>
              {priceEstimate.warehouse > 0 && (
                <div className="flex justify-between">
                  <span>Warehouse Fees:</span>
                  <span className="font-medium">{priceEstimate.warehouse} MAD</span>
                </div>
              )}
              {priceEstimate.fragile > 0 && (
                <div className="flex justify-between">
                  <span>Fragile Handling:</span>
                  <span className="font-medium">{priceEstimate.fragile} MAD</span>
                </div>
              )}
              {priceEstimate.insurance > 0 && (
                <div className="flex justify-between">
                  <span>Insurance:</span>
                  <span className="font-medium">{priceEstimate.insurance.toFixed(2)} MAD</span>
                </div>
              )}
              <div className="flex justify-between text-xs text-gray-600">
                <span>Service Multiplier:</span>
                <span>{priceEstimate.multiplier}x</span>
              </div>
              <div className="border-t-2 border-green-300 pt-2 mt-2">
                <div className="flex justify-between text-lg font-bold text-green-700">
                  <span>Total:</span>
                  <span>{priceEstimate.total} MAD</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Summary */}
        <div className="bg-gray-100 rounded-lg p-6">
          <h3 className="font-semibold mb-3">Order Summary</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Type:</span>
              <span className="font-medium">{isInterCity ? 'Inter-City' : 'Local'}</span>
            </div>
            <div className="flex justify-between">
              <span>Route:</span>
              <span className="font-medium">{formData.pickup_city} → {formData.delivery_city}</span>
            </div>
            <div className="flex justify-between">
              <span>Service:</span>
              <span className="font-medium capitalize">{formData.service_type}</span>
            </div>
            {isInterCity && (
              <>
                <div className="flex justify-between">
                  <span>Pickup:</span>
                  <span className="font-medium">{formData.pickup_option === 'door_pickup' ? 'Door Pickup' : 'Warehouse Dropoff'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Delivery:</span>
                  <span className="font-medium">{formData.delivery_option === 'door_delivery' ? 'Door Delivery' : 'Warehouse Pickup'}</span>
                </div>
              </>
            )}
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-primary w-full py-4 text-lg"
        >
          {loading ? 'Creating Order...' : `Create Order ${priceEstimate ? `- ${priceEstimate.total} MAD` : ''}`}
        </button>
      </form>
    </div>
  )
}
