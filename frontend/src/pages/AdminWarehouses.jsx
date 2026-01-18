import React, { useState, useEffect } from 'react'
import AdminNavbar from '../components/AdminNavbar'
import { Warehouse, Package, TrendingUp, MapPin, RefreshCw, Edit2, X, Save, Phone, User } from 'lucide-react'

export default function AdminWarehouses() {
  const [warehouses, setWarehouses] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedWarehouse, setSelectedWarehouse] = useState(null)
  const [editData, setEditData] = useState({})
  const [saving, setSaving] = useState(false)

  // Debug log
  console.log('AdminWarehouses v2.0 - Modern Modal Loaded')

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

  const openEditModal = (warehouse) => {
    setSelectedWarehouse(warehouse)
    setEditData({
      manager: warehouse.manager,
      phone: warehouse.phone,
      capacity: warehouse.capacity,
      status: warehouse.status || 'active'
    })
  }

  const closeModal = () => {
    setSelectedWarehouse(null)
    setEditData({})
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const token = localStorage.getItem('adminToken')
      await fetch(`http://localhost:8001/api/admin/warehouses/${selectedWarehouse.id}/update`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editData)
      })
      await fetchWarehouses()
      closeModal()
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setSaving(false)
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
        {/* Version marker for cache busting */}
        <div className="hidden" data-version="v2.0-modern-modal"></div>
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Warehouse Management</h1>
          <button onClick={fetchWarehouses} className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
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
                  <button
                    onClick={() => openEditModal(warehouse)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <Edit2 className="w-5 h-5 text-gray-600" />
                  </button>
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

      {/* Modern Edit Modal */}
      {selectedWarehouse && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 rounded-t-2xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Warehouse className="w-6 h-6" />
                  <h2 className="text-xl font-bold">Manage Warehouse</h2>
                </div>
                <button onClick={closeModal} className="p-1 hover:bg-white/20 rounded-lg transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <p className="text-purple-100 text-sm mt-2">{selectedWarehouse.city}</p>
            </div>

            {/* Content */}
            <div className="p-6 space-y-5">
              {/* Manager */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                  <User className="w-4 h-4 text-gray-500" />
                  Manager Name
                </label>
                <input
                  type="text"
                  value={editData.manager || ''}
                  onChange={(e) => setEditData({...editData, manager: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  placeholder="Enter manager name"
                />
              </div>

              {/* Phone */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                  <Phone className="w-4 h-4 text-gray-500" />
                  Phone Number
                </label>
                <input
                  type="tel"
                  value={editData.phone || ''}
                  onChange={(e) => setEditData({...editData, phone: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  placeholder="+212 XXX XXX XXX"
                />
              </div>

              {/* Capacity */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                  <Package className="w-4 h-4 text-gray-500" />
                  Max Capacity
                </label>
                <input
                  type="number"
                  value={editData.capacity || ''}
                  onChange={(e) => setEditData({...editData, capacity: parseInt(e.target.value)})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  placeholder="Enter max capacity"
                />
              </div>

              {/* Status */}
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                  <TrendingUp className="w-4 h-4 text-gray-500" />
                  Status
                </label>
                <select
                  value={editData.status || 'active'}
                  onChange={(e) => setEditData({...editData, status: e.target.value})}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                >
                  <option value="active">Active</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>

              {/* Info Box */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-blue-900">Location</p>
                    <p className="text-sm text-blue-700 mt-1">{selectedWarehouse.address}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="sticky bottom-0 bg-gray-50 px-6 py-4 rounded-b-2xl border-t border-gray-200 flex gap-3">
              <button
                onClick={closeModal}
                className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all font-medium flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {saving ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
