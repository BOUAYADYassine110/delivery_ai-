import { useState } from 'react'
import { useMutation } from 'react-query'
import { api } from '../services/api'
import { useNavigate } from 'react-router-dom'
import { Truck, MapPin, Package, Globe, Weight, Ruler } from 'lucide-react'

export default function CreateInterCityOrder() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    sender_address: '',
    receiver_address: '',
    origin_city: '',
    destination_city: '',
    package_description: '',
    weight: '',
    dimensions: { length: '', width: '', height: '' },
    service_type: 'standard',
    is_international: false,
    special_requirements: ''
  })

  const createMutation = useMutation(api.createInterCityOrder, {
    onSuccess: (response) => {
      alert(`Inter-city order created! Order ID: ${response.data.order_id}`)
      navigate('/dashboard')
    },
    onError: (error) => {
      alert(`Error creating order: ${error.response?.data?.detail || error.message}`)
    }
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    createMutation.mutate({
      ...formData,
      weight: parseFloat(formData.weight),
      dimensions: formData.dimensions.length ? {
        length: parseFloat(formData.dimensions.length),
        width: parseFloat(formData.dimensions.width),
        height: parseFloat(formData.dimensions.height)
      } : null
    })
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    if (name.startsWith('dim_')) {
      const dimName = name.replace('dim_', '')
      setFormData(prev => ({
        ...prev,
        dimensions: { ...prev.dimensions, [dimName]: value }
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      }))
    }
  }

  return (
    <div className="max-w-5xl mx-auto animate-fade-in">
      <div className="flex items-center gap-3 mb-8">
        <div className="p-3 bg-gradient-to-br from-green-500 to-teal-600 rounded-2xl">
          <Truck className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-teal-600 bg-clip-text text-transparent">
          Create Inter-City Order
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Origin & Destination Cities */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center gap-2 mb-4">
            <MapPin className="w-5 h-5 text-green-600" />
            <h3 className="font-bold text-lg">Route Information</h3>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Origin City</label>
              <input
                name="origin_city"
                placeholder="e.g., New York, NY"
                value={formData.origin_city}
                onChange={handleChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-green-500 focus:ring-4 focus:ring-green-100 focus:outline-none transition-all"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Destination City</label>
              <input
                name="destination_city"
                placeholder="e.g., Los Angeles, CA"
                value={formData.destination_city}
                onChange={handleChange}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-green-500 focus:ring-4 focus:ring-green-100 focus:outline-none transition-all"
                required
              />
            </div>
          </div>
        </div>

        {/* Addresses */}
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
            <div className="flex items-center gap-2 mb-4">
              <Package className="w-5 h-5 text-blue-600" />
              <h3 className="font-bold text-lg">Sender Details</h3>
            </div>
            <div className="space-y-4">
              <textarea
                name="sender_address"
                placeholder="Full sender address including street, city, state, ZIP"
                value={formData.sender_address}
                onChange={handleChange}
                rows={3}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 focus:outline-none transition-all resize-none"
                required
              />
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
            <div className="flex items-center gap-2 mb-4">
              <Package className="w-5 h-5 text-red-600" />
              <h3 className="font-bold text-lg">Receiver Details</h3>
            </div>
            <div className="space-y-4">
              <textarea
                name="receiver_address"
                placeholder="Full receiver address including street, city, state, ZIP"
                value={formData.receiver_address}
                onChange={handleChange}
                rows={3}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-red-500 focus:ring-4 focus:ring-red-100 focus:outline-none transition-all resize-none"
                required
              />
            </div>
          </div>
        </div>

        {/* Package Details */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
          <div className="flex items-center gap-2 mb-4">
            <Weight className="w-5 h-5 text-purple-600" />
            <h3 className="font-bold text-lg">Package Information</h3>
          </div>
          <div className="space-y-4">
            <textarea
              name="package_description"
              placeholder="Describe the package contents (e.g., electronics, documents, fragile items)"
              value={formData.package_description}
              onChange={handleChange}
              rows={2}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-4 focus:ring-purple-100 focus:outline-none transition-all resize-none"
              required
            />

            <div className="grid grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Weight (kg)</label>
                <input
                  name="weight"
                  type="number"
                  step="0.1"
                  placeholder="5.0"
                  value={formData.weight}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-4 focus:ring-purple-100 focus:outline-none transition-all"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Length (cm)</label>
                <input
                  name="dim_length"
                  type="number"
                  placeholder="30"
                  value={formData.dimensions.length}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-4 focus:ring-purple-100 focus:outline-none transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Width (cm)</label>
                <input
                  name="dim_width"
                  type="number"
                  placeholder="20"
                  value={formData.dimensions.width}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-4 focus:ring-purple-100 focus:outline-none transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Height (cm)</label>
                <input
                  name="dim_height"
                  type="number"
                  placeholder="10"
                  value={formData.dimensions.height}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-4 focus:ring-purple-100 focus:outline-none transition-all"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Service Options */}
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
            <div className="flex items-center gap-2 mb-4">
              <Globe className="w-5 h-5 text-orange-600" />
              <h3 className="font-bold text-lg">Service Options</h3>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Service Type</label>
                <select
                  name="service_type"
                  value={formData.service_type}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-4 focus:ring-orange-100 focus:outline-none transition-all"
                >
                  <option value="standard">Standard (3-5 days)</option>
                  <option value="express">Express (1-2 days)</option>
                  <option value="overnight">Overnight (next day)</option>
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  name="is_international"
                  checked={formData.is_international}
                  onChange={handleChange}
                  className="w-4 h-4 text-orange-600 bg-gray-100 border-gray-300 rounded focus:ring-orange-500"
                />
                <label className="text-sm font-medium text-gray-700">
                  International shipment (customs clearance required)
                </label>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
            <div className="flex items-center gap-2 mb-4">
              <Ruler className="w-5 h-5 text-indigo-600" />
              <h3 className="font-bold text-lg">Special Requirements</h3>
            </div>
            <textarea
              name="special_requirements"
              placeholder="Any special handling instructions (e.g., fragile, temperature controlled, hazardous materials)"
              value={formData.special_requirements}
              onChange={handleChange}
              rows={4}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 focus:outline-none transition-all resize-none"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={createMutation.isLoading}
          className="w-full bg-gradient-to-r from-green-600 to-teal-600 text-white py-4 rounded-xl hover:from-green-700 hover:to-teal-700 font-bold text-lg shadow-xl transform hover:scale-105 transition-all duration-300 disabled:opacity-50"
        >
          {createMutation.isLoading ? 'Creating Inter-City Order...' : 'Create Inter-City Order'}
        </button>
      </form>
    </div>
  )
}
