import { useState, useEffect } from 'react'
import { Package, Truck, Clock, DollarSign, TrendingUp, Plus, Minus } from 'lucide-react'

export default function MultiPackageManager({ driverId }) {
  const [capacity, setCapacity] = useState(null)
  const [batchOrders, setBatchOrders] = useState([])
  const [optimization, setOptimization] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (driverId) {
      fetchDriverCapacity()
    }
  }, [driverId])

  const fetchDriverCapacity = async () => {
    try {
      const response = await fetch(`http://localhost:8001/api/batch/driver/${driverId}/capacity`)
      const data = await response.json()
      setCapacity(data)
    } catch (error) {
      console.error('Failed to fetch capacity:', error)
    }
  }

  const optimizeRoute = async () => {
    setLoading(true)
    try {
      const response = await fetch(`http://localhost:8001/api/batch/optimize-existing/${driverId}`, {
        method: 'POST'
      })
      const data = await response.json()
      setOptimization(data)
      fetchDriverCapacity() // Refresh capacity
    } catch (error) {
      console.error('Failed to optimize route:', error)
    } finally {
      setLoading(false)
    }
  }

  const assignBatchOrders = async (orderIds) => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8001/api/batch/assign-multiple', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_ids: orderIds,
          driver_id: driverId
        })
      })
      const data = await response.json()
      if (data.success) {
        fetchDriverCapacity()
        setOptimization(data.route_optimization)
      }
    } catch (error) {
      console.error('Failed to assign batch:', error)
    } finally {
      setLoading(false)
    }
  }

  if (!capacity) {
    return (
      <div className="animate-pulse bg-gray-100 rounded-lg p-6">
        <div className="h-4 bg-gray-300 rounded w-1/2 mb-4"></div>
        <div className="h-8 bg-gray-300 rounded w-full"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Capacity Overview */}
      <div className="bg-white rounded-lg border p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Truck className="w-5 h-5 text-blue-600" />
          Multi-Package Capacity
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{capacity.current_load}</div>
            <div className="text-sm text-gray-600">Current Load</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{capacity.available_slots}</div>
            <div className="text-sm text-gray-600">Available Slots</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{capacity.max_capacity}</div>
            <div className="text-sm text-gray-600">Max Capacity</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{capacity.utilization_percentage}%</div>
            <div className="text-sm text-gray-600">Utilization</div>
          </div>
        </div>

        {/* Capacity Bar */}
        <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
          <div 
            className={`h-4 rounded-full transition-all duration-300 ${
              capacity.utilization_percentage > 90 ? 'bg-red-500' :
              capacity.utilization_percentage > 70 ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${capacity.utilization_percentage}%` }}
          ></div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={optimizeRoute}
            disabled={loading || capacity.current_load === 0}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <TrendingUp className="w-4 h-4" />
            )}
            Optimize Route
          </button>
          
          {capacity.can_accept_more && (
            <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Add More
            </button>
          )}
        </div>
      </div>

      {/* Current Route Optimization */}
      {capacity.current_route && (
        <div className="bg-white rounded-lg border p-6">
          <h4 className="font-semibold mb-4 flex items-center gap-2">
            <Package className="w-5 h-5 text-green-600" />
            Current Route Performance
          </h4>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium">Total Time</span>
              </div>
              <div className="text-xl font-bold text-blue-700">
                {Math.round(capacity.current_route.total_time)} min
              </div>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium">Distance</span>
              </div>
              <div className="text-xl font-bold text-green-700">
                {capacity.current_route.total_distance.toFixed(1)} km
              </div>
            </div>
            
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium">Cost</span>
              </div>
              <div className="text-xl font-bold text-purple-700">
                {capacity.current_route.total_cost.toFixed(2)} MAD
              </div>
            </div>
            
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-orange-600" />
                <span className="text-sm font-medium">Efficiency</span>
              </div>
              <div className="text-xl font-bold text-orange-700">
                {capacity.current_route.efficiency_score.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Optimization Results */}
      {optimization && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h4 className="font-semibold text-green-800 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Route Optimization Results
          </h4>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {optimization.improvements?.cost_savings?.toFixed(2) || 0} MAD
              </div>
              <div className="text-sm text-green-700">Cost Savings</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {optimization.improvements?.time_saved?.toFixed(1) || 0} min
              </div>
              <div className="text-sm text-blue-700">Time Saved</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                +{optimization.improvements?.efficiency_gain?.toFixed(1) || 0}%
              </div>
              <div className="text-sm text-purple-700">Efficiency Gain</div>
            </div>
          </div>

          <div className="bg-white rounded-lg p-4">
            <h5 className="font-medium mb-2">Optimization Summary</h5>
            <div className="text-sm text-gray-600 space-y-1">
              <div>Orders optimized: {optimization.orders_optimized}</div>
              <div>New total distance: {optimization.new_metrics?.distance?.toFixed(1)} km</div>
              <div>New total time: {Math.round(optimization.new_metrics?.time || 0)} minutes</div>
              <div>New total cost: {optimization.new_metrics?.cost?.toFixed(2)} MAD</div>
            </div>
          </div>
        </div>
      )}

      {/* Vehicle Type Info */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h5 className="font-medium text-gray-900 mb-2">Vehicle Specifications</h5>
        <div className="text-sm text-gray-600 space-y-1">
          <div>Type: <span className="font-medium capitalize">{capacity.vehicle_type}</span></div>
          <div>Max Packages: <span className="font-medium">{capacity.max_capacity}</span></div>
          <div>Optimization: <span className="font-medium">TSP Algorithm</span></div>
          <div>Cost Reduction: <span className="font-medium">Up to 40%</span></div>
        </div>
      </div>
    </div>
  )
}