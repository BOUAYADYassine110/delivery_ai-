import React, { useState, useEffect } from 'react'
import { DollarSign, Package, Truck, MapPin, Clock, Calculator, Sparkles } from 'lucide-react'
import CustomerNavbar from '../components/CustomerNavbar'
import pricingService from '../services/pricingService'

export default function PricingCalculator() {
  const [formData, setFormData] = useState({
    pickup_city: 'Casablanca',
    delivery_city: 'Casablanca',
    weight: '',
    length: '',
    width: '',
    height: '',
    service_type: 'standard',
    fragile: false,
    insurance_value: 0
  })
  const [priceEstimate, setPriceEstimate] = useState(null)
  const [loading, setLoading] = useState(false)
  const [aiPowered, setAiPowered] = useState(false)

  const cities = ['Casablanca', 'Rabat', 'Marrakech', 'El Jadida', 'Salé', 'Agadir']
  const isInterCity = formData.pickup_city !== formData.delivery_city

  useEffect(() => {
    if (formData.weight && formData.length && formData.width && formData.height) {
      calculatePrice()
    }
  }, [formData])

  const calculatePrice = async () => {
    setLoading(true)
    const weight = parseFloat(formData.weight) || 1
    
    try {
      // Use AI pricing service
      const result = await pricingService.calculatePrice(
        formData.pickup_city,
        formData.delivery_city,
        weight,
        formData.service_type
      )
      
      const basePrice = result.price
      setAiPowered(result.method === 'ai_agent')
      
      // Calculate additional fees - MOROCCAN RATES
      const volume = (parseFloat(formData.length) * parseFloat(formData.width) * parseFloat(formData.height)) / 1000000
      const volumeCost = volume * 5  // Reduced from 50 to 5 MAD per cubic meter
      const insuranceFee = parseFloat(formData.insurance_value) * 0.01  // Reduced from 0.02 to 0.01
      const fragileFee = formData.fragile ? 15 : 0  // Reduced from 25 to 15
      
      const total = basePrice + volumeCost + insuranceFee + fragileFee
      
      const estimatedDays = isInterCity 
        ? (formData.service_type === 'express' ? 1 : 3)
        : (formData.service_type === 'express' ? 0 : 1)
      
      setPriceEstimate({
        base: basePrice,
        volume: volumeCost,
        insurance: insuranceFee,
        fragile: fragileFee,
        total: Math.round(total * 100) / 100,
        estimatedDays,
        method: result.method,
        aiAnalysis: result.aiAnalysis
      })
    } catch (error) {
      console.error('Price calculation error:', error)
      // Fallback to local calculation - MOROCCAN RATES
      const basePrice = isInterCity ? 30 : 15  // MAD
      const weightCost = weight * 2  // 2 MAD per kg
      const volume = (parseFloat(formData.length) * parseFloat(formData.width) * parseFloat(formData.height)) / 1000000
      const volumeCost = volume * 5  // 5 MAD per cubic meter
      const insuranceFee = parseFloat(formData.insurance_value) * 0.01  // 1%
      const fragileFee = formData.fragile ? 15 : 0  // 15 MAD
      const serviceMultiplier = formData.service_type === 'express' ? 1.3 : 1.0  // Reduced from 1.5
      const subtotal = basePrice + weightCost + volumeCost + insuranceFee + fragileFee
      const total = subtotal * serviceMultiplier
      
      setPriceEstimate({
        base: basePrice,
        weight: weightCost,
        volume: volumeCost,
        insurance: insuranceFee,
        fragile: fragileFee,
        multiplier: serviceMultiplier,
        subtotal: Math.round(subtotal * 100) / 100,
        total: Math.round(total * 100) / 100,
        estimatedDays: isInterCity ? (formData.service_type === 'express' ? 1 : 3) : (formData.service_type === 'express' ? 0 : 1),
        method: 'fallback'
      })
      setAiPowered(false)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <CustomerNavbar />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
              <Calculator className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Pricing Calculator</h1>
          </div>
          <p className="text-gray-600">Estimate your delivery cost before placing an order</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Input Form */}
          <div className="space-y-6">
            {/* Route */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <MapPin className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-lg">Route</h3>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Pickup City</label>
                  <select
                    value={formData.pickup_city}
                    onChange={(e) => setFormData({...formData, pickup_city: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {cities.map(city => (
                      <option key={city} value={city}>{city}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Delivery City</label>
                  <select
                    value={formData.delivery_city}
                    onChange={(e) => setFormData({...formData, delivery_city: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {cities.map(city => (
                      <option key={city} value={city}>{city}</option>
                    ))}
                  </select>
                </div>
                {isInterCity && (
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center gap-2">
                    <Truck className="w-5 h-5 text-amber-600" />
                    <span className="text-sm text-amber-800 font-medium">Inter-City Delivery</span>
                  </div>
                )}
              </div>
            </div>

            {/* Package Details */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <Package className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-lg">Package Details</h3>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Weight (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    placeholder="5.0"
                    value={formData.weight}
                    onChange={(e) => setFormData({...formData, weight: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Length (cm)</label>
                    <input
                      type="number"
                      placeholder="30"
                      value={formData.length}
                      onChange={(e) => setFormData({...formData, length: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Width (cm)</label>
                    <input
                      type="number"
                      placeholder="20"
                      value={formData.width}
                      onChange={(e) => setFormData({...formData, width: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Height (cm)</label>
                    <input
                      type="number"
                      placeholder="10"
                      value={formData.height}
                      onChange={(e) => setFormData({...formData, height: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Service Options */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <Truck className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-lg">Service Options</h3>
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <label className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                    formData.service_type === 'standard' ? 'border-blue-600 bg-blue-50' : 'border-gray-300'
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
                    formData.service_type === 'express' ? 'border-blue-600 bg-blue-50' : 'border-gray-300'
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
                      <div className="text-xs text-amber-600 font-medium mt-1">1.5x price</div>
                    </div>
                  </label>
                </div>
                <label className="flex items-center p-3 border-2 border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
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
                  <label className="block text-sm font-medium text-gray-700 mb-2">Insurance Value (MAD)</label>
                  <input
                    type="number"
                    placeholder="0"
                    value={formData.insurance_value}
                    onChange={(e) => setFormData({...formData, insurance_value: e.target.value})}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  <div className="text-xs text-gray-500 mt-1">2% of declared value</div>
                </div>
              </div>
            </div>
          </div>

          {/* Price Estimate */}
          <div className="lg:sticky lg:top-24 h-fit">
            {priceEstimate ? (
              <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl shadow-xl p-6 text-white">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-6 h-6" />
                    <h3 className="font-semibold text-xl">Price Estimate</h3>
                  </div>
                  {aiPowered && (
                    <div className="flex items-center gap-1 bg-blue-500 px-3 py-1 rounded-full text-xs">
                      <Sparkles className="w-3 h-3" />
                      <span>AI Powered</span>
                    </div>
                  )}
                </div>
                <div className="space-y-3 mb-6">
                  <div className="flex justify-between text-blue-100">
                    <span>Base Price:</span>
                    <span className="font-medium text-white">{priceEstimate.base} MAD</span>
                  </div>
                  {priceEstimate.weight && (
                    <div className="flex justify-between text-blue-100">
                      <span>Weight Cost:</span>
                      <span className="font-medium text-white">{priceEstimate.weight.toFixed(2)} MAD</span>
                    </div>
                  )}
                  <div className="flex justify-between text-blue-100">
                    <span>Volume Cost:</span>
                    <span className="font-medium text-white">{priceEstimate.volume.toFixed(2)} MAD</span>
                  </div>
                  {priceEstimate.fragile > 0 && (
                    <div className="flex justify-between text-blue-100">
                      <span>Fragile Handling:</span>
                      <span className="font-medium text-white">{priceEstimate.fragile} MAD</span>
                    </div>
                  )}
                  {priceEstimate.insurance > 0 && (
                    <div className="flex justify-between text-blue-100">
                      <span>Insurance:</span>
                      <span className="font-medium text-white">{priceEstimate.insurance.toFixed(2)} MAD</span>
                    </div>
                  )}
                  {priceEstimate.multiplier && (
                    <div className="border-t border-blue-400 pt-3">
                      <div className="flex justify-between text-blue-100 text-sm">
                        <span>Subtotal:</span>
                        <span className="font-medium text-white">{priceEstimate.subtotal} MAD</span>
                      </div>
                      <div className="flex justify-between text-blue-100 text-sm mt-2">
                        <span>Service Multiplier:</span>
                        <span className="font-medium text-white">{priceEstimate.multiplier}x</span>
                      </div>
                    </div>
                  )}
                </div>
                <div className="bg-white rounded-xl p-4 mb-6">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-700 font-semibold">Total Cost:</span>
                    <span className="text-3xl font-bold text-blue-600">{priceEstimate.total} MAD</span>
                  </div>
                </div>
                <div className="bg-blue-500 rounded-xl p-4 flex items-center gap-3">
                  <Clock className="w-5 h-5" />
                  <div>
                    <div className="font-semibold">Estimated Delivery</div>
                    <div className="text-sm text-blue-100">
                      {priceEstimate.estimatedDays === 0 ? 'Same day' : `${priceEstimate.estimatedDays} ${priceEstimate.estimatedDays === 1 ? 'day' : 'days'}`}
                    </div>
                  </div>
                </div>
                {priceEstimate.method && (
                  <div className="mt-4 text-xs text-blue-200 text-center">
                    Calculated using: {priceEstimate.method === 'ai_agent' ? 'AI Agent' : priceEstimate.method === 'formula' ? 'Standard Formula' : 'Fallback Method'}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
                <Calculator className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Enter Package Details</h3>
                <p className="text-gray-600">Fill in the form to calculate your delivery cost</p>
                {loading && (
                  <div className="mt-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="text-sm text-gray-500 mt-2">Calculating with AI...</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
