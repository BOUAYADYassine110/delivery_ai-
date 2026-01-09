import React, { useState, useEffect } from 'react'
import AdminNavbar from '../components/AdminNavbar'
import { Warehouse, Package, TrendingUp, MapPin, RefreshCw } from 'lucide-react'

export default function AdminWarehouses() {
  const [warehouses, setWarehouses] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchWarehouses()
  }, [])

  const fetchWarehouses = async () => {
    try {
      const token = localStorage.getItem('adminToken')
      const response = await fetch('http://localhost:8001/api/warehouses', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await response.json()
      setWarehouses(data)
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const getCapacityColor = (percentage) => {
    if (percentage >= 80) return 'text-red-600 bg-red-100'
    if (percentage >= 60) return 'text-yellow-600 bg-yellow-100'
    return 'text-green-600 bg-green-100'
  }

  if (loading) return <div className="flex items-center justify-center h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div></div>

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminNavbar />
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Warehouse Management</h1>
          <button onClick={fetchWarehouses} className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Warehouses</p>
                <p className="text-2xl font-bold text-gray-900">{warehouses.length}</p>
              </div>
              <Warehouse className="w-8 h-8 text-purple-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Packages</p>
                <p className="text-2xl font-bold text-gray-900">{warehouses.reduce((sum, w) => sum + w.current_packages, 0)}</p>
              </div>
              <Package className="w-8 h-8 text-blue-600" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Capacity</p>
                <p className="text-2xl font-bold text-gray-900">
                  {(warehouses.reduce((sum, w) => sum + (w.current_packages / w.capacity * 100), 0) / warehouses.length || 0).toFixed(0)}%
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {warehouses.map(warehouse => {
            const capacityPercentage = (warehouse.current_packages / warehouse.capacity * 100).toFixed(0)
            return (
              <div key={warehouse.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">{warehouse.city}</h3>
                    <div className="flex items-center gap-2 text-sm text-gray-600 mt-1">
                      <MapPin className="w-4 h-4" />
                      {warehouse.address}
                    </div>
                  </div>
                  <Warehouse className="w-8 h-8 text-purple-600" />
                </div>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-gray-600">Capacity</span>
                      <span className={`font-semibold px-2 py-1 rounded ${getCapacityColor(capacityPercentage)}`}>
                        {capacityPercentage}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className={`h-2 rounded-full ${capacityPercentage >= 80 ? 'bg-red-600' : capacityPercentage >= 60 ? 'bg-yellow-600' : 'bg-green-600'}`} style={{ width: `${capacityPercentage}%` }}></div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                    <div>
                      <p className="text-sm text-gray-600">Current Packages</p>
                      <p className="text-lg font-bold text-gray-900">{warehouse.current_packages}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Max Capacity</p>
                      <p className="text-lg font-bold text-gray-900">{warehouse.capacity}</p>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
