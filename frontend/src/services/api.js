import axios from 'axios'

const API_BASE = 'http://localhost:8001/api'

axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('token') || localStorage.getItem('driver_token') || localStorage.getItem('admin_token')
  if (token && token !== 'undefined' && token !== 'null') {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error)
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('driver_token')
      localStorage.removeItem('admin_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const api = {
  // Auth
  login: (data) => axios.post(`${API_BASE}/auth/login`, data),
  register: (data) => axios.post(`${API_BASE}/auth/register`, data),
  getMe: () => axios.get(`${API_BASE}/auth/me`),
  
  // Orders
  createOrder: (data) => axios.post(`${API_BASE}/orders`, data),
  getOrders: () => {
    console.log('Fetching orders from:', `${API_BASE}/orders`)
    return axios.get(`${API_BASE}/orders`)
  },
  getOrder: (id) => axios.get(`${API_BASE}/orders/${id}`),
  trackOrder: (trackingNumber) => axios.get(`${API_BASE}/orders/tracking/${trackingNumber}`),
  trackOrderById: (orderId) => axios.get(`${API_BASE}/orders/${orderId}/track`),
  getTrackingEvents: (orderId) => axios.get(`${API_BASE}/tracking/${orderId}`),
  updateOrderLocation: (orderId, location) => axios.post(`${API_BASE}/orders/${orderId}/location`, location),
  updateDeliveryStatus: (orderId, update) => axios.post(`${API_BASE}/orders/${orderId}/status`, update),
  calculatePrice: (data) => axios.post(`${API_BASE}/pricing/calculate`, data),
  getAgentStatus: () => axios.get(`${API_BASE}/agents/status`),

  // Cities and Locations
  getCities: () => axios.get(`${API_BASE}/cities`),
  getWarehouses: () => axios.get(`${API_BASE}/warehouses`),

  // Inter-City Operations
  createInterCityOrder: (data) => axios.post(`${API_BASE}/inter-city/orders`, data),
  trackInterCityOrder: (trackingNumber) => axios.get(`${API_BASE}/inter-city/track/${trackingNumber}`),
  warehouseDropoff: (orderId, data) => axios.post(`${API_BASE}/inter-city/warehouse-dropoff/${orderId}`, data),
  processWarehousePackage: (orderId) => axios.post(`${API_BASE}/inter-city/process-warehouse/${orderId}`),
  
  // Driver Interface
  driverLogin: (data) => axios.post(`${API_BASE}/driver/login`, data),
  getDriverDashboard: (driverId) => axios.get(`${API_BASE}/driver/${driverId}/dashboard`),
  updateDriverLocation: (driverId, location) => axios.post(`${API_BASE}/driver/${driverId}/location`, location),
  getDriverRoute: (driverId) => axios.get(`${API_BASE}/driver/${driverId}/route`),
  acceptAssignment: (driverId, data) => axios.post(`${API_BASE}/driver/${driverId}/accept-assignment`, data),
  startDelivery: (driverId, orderId) => axios.post(`${API_BASE}/driver/${driverId}/start-delivery/${orderId}`),
  completeDelivery: (driverId, data) => axios.post(`${API_BASE}/driver/${driverId}/complete-delivery`, data),
  respondToAssignment: (data) => axios.post(`${API_BASE}/driver/assignment/response`, data),
  updateGPS: (data) => axios.post(`${API_BASE}/driver/gps/update`, data),
  startDeliveryRoute: (orderId, data) => axios.post(`${API_BASE}/driver/delivery/start/${orderId}`, data),
  completeDeliveryFinal: (data) => axios.post(`${API_BASE}/driver/delivery/complete`, data),
  getDriverRoute: (driverId) => axios.get(`${API_BASE}/driver/${driverId}/route`),
  updateDriverStatus: (driverId, data) => axios.post(`${API_BASE}/driver/${driverId}/update-status`, data),

  // Admin Interface
  adminLogin: (data) => axios.post(`${API_BASE}/admin/login`, data),
  getAdminOrders: () => axios.get(`${API_BASE}/admin/orders`),
  getAdminDrivers: () => axios.get(`${API_BASE}/admin/drivers`),
  getAdminAnalytics: () => axios.get(`${API_BASE}/admin/analytics`),
  
  // Enhanced tracking
  getWeather: (city) => axios.get(`${API_BASE}/weather/${city}`),
  getRouteInfo: (pickupCity, deliveryCity) => axios.get(`${API_BASE}/route/${pickupCity}/${deliveryCity}`),
  
  // Enhanced Admin Features
  getLiveMap: () => axios.get(`${API_BASE}/admin/live-map`),
  getAdvancedAnalytics: () => axios.get(`${API_BASE}/admin/analytics/advanced`),
  suspendDriver: (driverId, data) => axios.post(`${API_BASE}/admin/driver/${driverId}/suspend`, data),
  getEmergencies: () => axios.get(`${API_BASE}/admin/emergencies`),
  
  // Enhanced Driver Features
  updateDriverStatus: (data) => axios.post(`${API_BASE}/driver/status/update`, data),
  getDriverEarnings: (driverId) => axios.get(`${API_BASE}/driver/${driverId}/earnings`),
  submitProofOfDelivery: (data) => axios.post(`${API_BASE}/driver/proof-of-delivery`, data),
  sendEmergencyAlert: (data) => axios.post(`${API_BASE}/driver/emergency`, data),
  
  // Customer Features
  rateDriver: (data) => axios.post(`${API_BASE}/customer/rate-driver`, data),
  
  // Chat System
  sendChatMessage: (data) => axios.post(`${API_BASE}/chat/send`, data),
  getChatMessages: (userId) => axios.get(`${API_BASE}/chat/${userId}`),
  
  // Payment System
  processPayment: (data) => axios.post(`${API_BASE}/payment/process`, data),
  
  // AI Features
  getOptimizedRoutes: () => axios.get(`${API_BASE}/ai/optimize-routes`),
  getPredictiveAnalytics: () => axios.get(`${API_BASE}/analytics/predictions`),
  
  // Multi-language
  getTranslations: (language) => axios.get(`${API_BASE}/translations/${language}`),
  
  // Enhanced Notifications
  markNotificationRead: (notificationId) => axios.post(`${API_BASE}/notifications/${notificationId}/read`)
}
