import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Package, MapPin, User, Phone, Weight, Box, Truck } from 'lucide-react'
import MapPicker from '../components/MapPicker'

export default function CreateOrder() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [showPickupMap, setShowPickupMap] = useState(false)
  const [showDeliveryMap, setShowDeliveryMap] = useState(false)
  const [formData, setFormData] = useState({
    sender_name: '',
    sender_phone: '',
    pickup_address: '',
    pickup_city: 'Casablanca',
    receiver_name: '',
    receiver_phone: '',
    delivery_address: '',
    delivery_city: 'Casablanca',
    weight: '',
    length: '',
    width: '',
    height: '',
    package_description: '',
    service_type: 'standard'
  })

  const cities = ['Casablanca', 'Rabat', 'Marrakech', 'El Jadida', 'Salé', 'Agadir']
  const isInterCity = formData.pickup_city !== formData.delivery_city

  // Auto-set express for same city
  useEffect(() => {
    if (!isInterCity && formData.service_type === 'standard') {
      setFormData(prev => ({ ...prev, service_type: 'express' }))
    }
  }, [isInterCity])

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

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const orderData = {
        pickup_address: formData.pickup_address,
        delivery_address: formData.delivery_address,
        pickup_city: formData.pickup_city,
        delivery_city: formData.delivery_city,
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

      const response = await fetch('http://localhost:8001/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
      })

      if (response.ok) {
        const data = await response.json()
        alert(`Order created! Tracking: ${data.tracking_number}`)
        navigate('/dashboard')
      } else {
        alert('Failed to create order')
      }
    } catch (error) {
      alert('Error: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
            <Package className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Create Order</h1>
        </div>
        {isInterCity && (
          <div className="flex items-center gap-2 mt-4 px-4 py-2 bg-orange-100 text-orange-800 rounded-lg w-fit">
            <Truck className="w-5 h-5" />
            <span className="font-medium">Inter-City Delivery Detected</span>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Sender & Receiver */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Sender */}
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
                className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
              >
                <MapPin className="w-4 h-4" />
                {showPickupMap ? 'Hide Map' : 'Pick on Map'}
              </button>
              {showPickupMap && (
                <MapPicker
                  onLocationSelect={(loc) => setFormData({...formData, pickup_address: loc.address})}
                  initialPosition={[33.5731, -7.5898]}
                />
              )}
            </div>
          </div>

          {/* Receiver */}
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
                className="text-sm text-green-600 hover:text-green-700 font-medium flex items-center gap-1"
              >
                <MapPin className="w-4 h-4" />
                {showDeliveryMap ? 'Hide Map' : 'Pick on Map'}
              </button>
              {showDeliveryMap && (
                <MapPicker
                  onLocationSelect={(loc) => setFormData({...formData, delivery_address: loc.address})}
                  initialPosition={[33.5731, -7.5898]}
                />
              )}
            </div>
          </div>
        </div>

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
            className="input"
            required
          />
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
                <div className="text-sm text-gray-600">2-3 days</div>
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
                <div className="text-sm text-gray-600">Same day</div>
              </div>
            </label>
          </div>
        </div>

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
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn-primary w-full"
        >
          {loading ? 'Creating...' : 'Create Order'}
        </button>
      </form>
    </div>
  )
}
