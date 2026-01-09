/**
 * AI Pricing Service
 * Handles AI-powered price calculations for orders
 */

const API_BASE = 'http://localhost:8001'

export const pricingService = {
  /**
   * Calculate price using AI agent
   */
  async calculatePrice(pickupCity, deliveryCity, weight, serviceType = 'standard') {
    try {
      const response = await fetch(
        `${API_BASE}/api/pricing/calculate?pickup_city=${pickupCity}&delivery_city=${deliveryCity}&weight=${weight}&service_type=${serviceType}`
      )
      
      if (!response.ok) {
        throw new Error('Failed to calculate price')
      }
      
      const data = await response.json()
      return {
        success: true,
        price: data.total_cost,
        method: data.pricing_method,
        aiAnalysis: data.ai_analysis,
        isInterCity: data.is_inter_city,
        distance: data.distance_km,
        details: data
      }
    } catch (error) {
      console.error('Pricing calculation error:', error)
      // Fallback to local calculation
      return {
        success: false,
        price: calculateFallbackPrice(pickupCity, deliveryCity, weight, serviceType),
        method: 'fallback',
        error: error.message
      }
    }
  },

  /**
   * Get detailed price breakdown
   */
  async getPriceBreakdown(orderData) {
    const isInterCity = orderData.pickup_city !== orderData.delivery_city
    const weight = parseFloat(orderData.weight) || 1
    
    try {
      const result = await this.calculatePrice(
        orderData.pickup_city,
        orderData.delivery_city,
        weight,
        orderData.service_type
      )
      
      // Add additional fees
      let additionalFees = 0
      
      if (isInterCity) {
        if (orderData.pickup_option === 'warehouse_dropoff') additionalFees += 15
        if (orderData.delivery_option === 'warehouse_pickup') additionalFees += 15
      }
      
      if (orderData.fragile) additionalFees += 25
      if (orderData.insurance_value) additionalFees += orderData.insurance_value * 0.02
      
      const total = result.price + additionalFees
      
      return {
        basePrice: result.price,
        additionalFees,
        total: Math.round(total * 100) / 100,
        method: result.method,
        aiAnalysis: result.aiAnalysis,
        breakdown: {
          aiCalculated: result.price,
          warehouseFees: isInterCity ? (orderData.pickup_option === 'warehouse_dropoff' ? 15 : 0) + (orderData.delivery_option === 'warehouse_pickup' ? 15 : 0) : 0,
          fragileFee: orderData.fragile ? 25 : 0,
          insuranceFee: orderData.insurance_value ? orderData.insurance_value * 0.02 : 0
        }
      }
    } catch (error) {
      console.error('Price breakdown error:', error)
      return null
    }
  }
}

/**
 * Fallback price calculation (client-side)
 */
function calculateFallbackPrice(pickupCity, deliveryCity, weight, serviceType) {
  const isInterCity = pickupCity !== deliveryCity
  
  let basePrice = isInterCity ? 50 : 15
  let weightCost = isInterCity ? weight * 4 : weight * 2
  let distanceCost = isInterCity ? 20 : 10
  
  const serviceMultiplier = serviceType === 'express' ? 1.5 : 1.0
  
  return Math.round((basePrice + weightCost + distanceCost) * serviceMultiplier * 100) / 100
}

export default pricingService
