import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { X, Loader, AlertCircle, CheckCircle, TrendingUp, Users, Package, DollarSign } from 'lucide-react';
import AdminNavbar from '../components/AdminNavbar';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

const getVehicleIcon = (vehicleType) => {
  const icons = {
    'bike': '🚴',
    'scooter': '🛵',
    'car': '🚗',
    'van': '🚐',
    'truck': '🚚'
  };
  return icons[vehicleType.toLowerCase()] || '🚗';
};

const createCustomIcon = (vehicleType, status) => {
  const icon = getVehicleIcon(vehicleType);
  const color = status === 'online' ? '#10b981' : '#ef4444';
  return L.divIcon({
    html: `<div style="font-size: 24px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">${icon}</div>`,
    className: 'custom-marker',
    iconSize: [30, 30],
    iconAnchor: [15, 15]
  });
};

const createWarehouseIcon = () => {
  return L.divIcon({
    html: `<div style="font-size: 32px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">🏪</div>`,
    className: 'warehouse-marker',
    iconSize: [40, 40],
    iconAnchor: [20, 20]
  });
};

const AdminDashboard = () => {
  const [orders, setOrders] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [activeTab, setActiveTab] = useState('overview');
  const [liveMapData, setLiveMapData] = useState({ drivers: [], orders: [] });
  const [advancedAnalytics, setAdvancedAnalytics] = useState(null);
  const [warehouses, setWarehouses] = useState([]);
  const [showWarehouseModal, setShowWarehouseModal] = useState(false);
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);
  const [showReassignModal, setShowReassignModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [driverRecommendations, setDriverRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [ordersRes, driversRes, analyticsRes, liveMapRes, advAnalyticsRes, warehousesRes] = await Promise.all([
        api.getAdminOrders(),
        api.getAdminDrivers(),
        api.getAdminAnalytics(),
        api.getLiveMap().catch(() => ({ data: { drivers: [], orders: [] } })),
        api.getAdvancedAnalytics().catch(() => ({ data: null })),
        api.getWarehouses().catch(() => ({ data: [] }))
      ]);
      setOrders(ordersRes.data.orders || []);
      setDrivers(driversRes.data.drivers || []);
      setAnalytics(analyticsRes.data || {});
      setLiveMapData(liveMapRes.data);
      setAdvancedAnalytics(advAnalyticsRes.data);
      setWarehouses(Array.isArray(warehousesRes.data) ? warehousesRes.data : []);
    } catch (error) {
      console.error('Error fetching admin data:', error);
      showNotification('Error loading data', 'error');
    }
  };

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const handleAIReassign = async (orderId) => {
    setLoading(true);
    try {
      const response = await api.autoReassignOrder(orderId);
      showNotification(response.data.message, 'success');
      fetchData();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Failed to reassign order', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleManualReassign = async (orderId) => {
    setLoading(true);
    try {
      const response = await api.getDriverRecommendations(orderId);
      setDriverRecommendations(response.data.recommendations);
      setSelectedOrder(orderId);
      setShowReassignModal(true);
    } catch (error) {
      showNotification('Failed to load driver recommendations', 'error');
    } finally {
      setLoading(false);
    }
  };

  const confirmManualReassign = async (driverId) => {
    setLoading(true);
    try {
      await api.manualReassignOrder(selectedOrder, {
        order_id: selectedOrder,
        new_driver_id: driverId,
        reason: 'Manual admin reassignment'
      });
      showNotification('Order reassigned successfully', 'success');
      setShowReassignModal(false);
      fetchData();
    } catch (error) {
      showNotification('Failed to reassign order', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelOrder = async (orderId) => {
    if (!confirm('Are you sure you want to cancel this order?')) return;
    setLoading(true);
    try {
      await api.cancelOrder(orderId, 'Admin cancellation');
      showNotification('Order cancelled successfully', 'success');
      fetchData();
    } catch (error) {
      showNotification('Failed to cancel order', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSuspendDriver = async (driverId, suspend) => {
    const reason = suspend ? prompt('Enter suspension reason:') : '';
    if (suspend && !reason) return;
    setLoading(true);
    try {
      await api.suspendDriver(driverId, { suspend, reason });
      showNotification(`Driver ${suspend ? 'suspended' : 'activated'} successfully`, 'success');
      fetchData();
    } catch (error) {
      showNotification('Failed to update driver status', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateWarehouse = async (warehouseId, status) => {
    setLoading(true);
    try {
      await api.updateWarehouse(warehouseId, { status });
      showNotification('Warehouse updated successfully', 'success');
      fetchData();
      setShowWarehouseModal(false);
    } catch (error) {
      showNotification('Failed to update warehouse', 'error');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending_assignment': 'bg-yellow-100 text-yellow-800',
      'pending_acceptance': 'bg-orange-100 text-orange-800',
      'accepted': 'bg-blue-100 text-blue-800',
      'assigned': 'bg-blue-100 text-blue-800',
      'in_transit': 'bg-purple-100 text-purple-800',
      'delivered': 'bg-green-100 text-green-800',
      'available': 'bg-green-100 text-green-800',
      'online': 'bg-green-100 text-green-800',
      'busy': 'bg-red-100 text-red-800',
      'offline': 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminNavbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Notification Toast */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg flex items-center gap-3 animate-slide-in ${
          notification.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
        }`}>
          {notification.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
          <span className="font-medium">{notification.message}</span>
        </div>
      )}

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg shadow-xl flex items-center gap-3">
            <Loader className="animate-spin" size={24} />
            <span className="font-medium">Processing...</span>
          </div>
        </div>
      )}

      <div>
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl shadow-lg text-white transform hover:scale-105 transition-transform">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-blue-100 text-sm font-medium">Total Orders</p>
                      <p className="text-4xl font-bold mt-2">{analytics.total_orders || 0}</p>
                      <p className="text-blue-100 text-xs mt-1">All time</p>
                    </div>
                    <div className="bg-white/20 p-4 rounded-lg">
                      <Package size={32} />
                    </div>
                  </div>
                </div>
                <div className="bg-gradient-to-br from-yellow-500 to-orange-500 p-6 rounded-xl shadow-lg text-white transform hover:scale-105 transition-transform">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-yellow-100 text-sm font-medium">Pending</p>
                      <p className="text-4xl font-bold mt-2">{analytics.pending_orders || 0}</p>
                      <p className="text-yellow-100 text-xs mt-1">Awaiting assignment</p>
                    </div>
                    <div className="bg-white/20 p-4 rounded-lg">
                      <AlertCircle size={32} />
                    </div>
                  </div>
                </div>
                <div className="bg-gradient-to-br from-green-500 to-emerald-600 p-6 rounded-xl shadow-lg text-white transform hover:scale-105 transition-transform">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-100 text-sm font-medium">Completed</p>
                      <p className="text-4xl font-bold mt-2">{analytics.completed || 0}</p>
                      <p className="text-green-100 text-xs mt-1">Successfully delivered</p>
                    </div>
                    <div className="bg-white/20 p-4 rounded-lg">
                      <CheckCircle size={32} />
                    </div>
                  </div>
                </div>
                <div className="bg-gradient-to-br from-purple-500 to-indigo-600 p-6 rounded-xl shadow-lg text-white transform hover:scale-105 transition-transform">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-purple-100 text-sm font-medium">Active Drivers</p>
                      <p className="text-4xl font-bold mt-2">{analytics.active_drivers || 0}</p>
                      <p className="text-purple-100 text-xs mt-1">Online now</p>
                    </div>
                    <div className="bg-white/20 p-4 rounded-lg">
                      <Users size={32} />
                    </div>
                  </div>
                </div>
              </div>

              {advancedAnalytics && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">💰 Revenue Overview</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-4 bg-green-50 rounded-lg">
                        <span className="text-gray-700 font-medium">Total Revenue</span>
                        <span className="text-2xl font-bold text-green-600">{advancedAnalytics.revenue?.total || 0} MAD</span>
                      </div>
                      <div className="flex justify-between items-center p-4 bg-blue-50 rounded-lg">
                        <span className="text-gray-700 font-medium">Today's Revenue</span>
                        <span className="text-2xl font-bold text-blue-600">{advancedAnalytics.revenue?.today || 0} MAD</span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">🚗 Fleet Status</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <span className="text-gray-700">Total Drivers</span>
                        <span className="font-bold text-gray-900">{advancedAnalytics.fleet_status?.total_drivers || 0}</span>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                        <span className="text-gray-700">Online</span>
                        <span className="font-bold text-green-600">{advancedAnalytics.fleet_status?.online_drivers || 0}</span>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                        <span className="text-gray-700">Busy</span>
                        <span className="font-bold text-red-600">{advancedAnalytics.fleet_status?.busy_drivers || 0}</span>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-gray-100 rounded-lg">
                        <span className="text-gray-700">Offline</span>
                        <span className="font-bold text-gray-600">{advancedAnalytics.fleet_status?.offline_drivers || 0}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'live-map' && (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-gray-900">🗺️ Real-Time Tracking</h3>
                <div className="flex gap-2">
                  <div className="flex items-center gap-2 px-3 py-1 bg-green-50 rounded-lg">
                    <span className="text-xl">🚗</span>
                    <span className="text-sm font-medium text-green-700">{liveMapData.drivers.length} Drivers</span>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1 bg-purple-50 rounded-lg">
                    <span className="text-xl">🏪</span>
                    <span className="text-sm font-medium text-purple-700">{Array.isArray(warehouses) ? warehouses.length : 0} Warehouses</span>
                  </div>
                </div>
              </div>
              <div className="h-[600px] rounded-lg overflow-hidden">
                <MapContainer center={[33.5731, -7.5898]} zoom={6} style={{ height: '100%', width: '100%' }}>
                  <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                  {liveMapData.drivers.map(driver => (
                    <Marker 
                      key={driver.id} 
                      position={[driver.location.lat, driver.location.lng]}
                      icon={createCustomIcon(driver.vehicle_type, driver.status)}
                    >
                      <Popup>
                        <div className="text-sm">
                          <p className="font-bold">{getVehicleIcon(driver.vehicle_type)} {driver.name}</p>
                          <p>Status: <span className={driver.status === 'online' ? 'text-green-600' : 'text-red-600'}>{driver.status}</span></p>
                          <p>Vehicle: {driver.vehicle_type}</p>
                          <p>Orders: {driver.current_orders}</p>
                          <p>Rating: ⭐ {driver.rating}</p>
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                  {Array.isArray(warehouses) && warehouses.map(warehouse => (
                    <Marker
                      key={warehouse.id}
                      position={[warehouse.location.lat, warehouse.location.lng]}
                      icon={createWarehouseIcon()}
                    >
                      <Popup>
                        <div className="text-sm">
                          <p className="font-bold text-lg">🏪 {warehouse.name}</p>
                          <p className="text-gray-600">{warehouse.city}</p>
                          <p className="text-gray-600">{warehouse.address}</p>
                          <p className="mt-2">Capacity: <span className="font-semibold">{warehouse.current_packages || 0}/{warehouse.capacity}</span></p>
                          <p>Status: <span className={`font-semibold ${warehouse.status === 'operational' ? 'text-green-600' : 'text-red-600'}`}>{warehouse.status}</span></p>
                          <button 
                            onClick={() => { setSelectedWarehouse(warehouse); setShowWarehouseModal(true); }}
                            className="mt-2 w-full bg-blue-600 text-white px-3 py-1 rounded text-xs hover:bg-blue-700"
                          >
                            Manage
                          </button>
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                </MapContainer>
              </div>
            </div>
          )}

          {activeTab === 'warehouses' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-bold text-gray-900">🏪 Warehouse Management</h3>
                  <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium">
                    + Add Warehouse
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
                {Array.isArray(warehouses) && warehouses.length > 0 ? warehouses.map(warehouse => {
                  const utilizationPercent = warehouse.capacity > 0 ? (warehouse.current_packages / warehouse.capacity * 100) : 0;
                  return (
                    <div key={warehouse.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-bold text-gray-900 text-lg">{warehouse.name}</h4>
                          <p className="text-sm text-gray-600">{warehouse.city}</p>
                        </div>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          warehouse.status === 'operational' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {warehouse.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-3">{warehouse.address}</p>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Capacity</span>
                          <span className="font-semibold">{warehouse.current_packages || 0}/{warehouse.capacity}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${
                              utilizationPercent > 80 ? 'bg-red-500' : 
                              utilizationPercent > 50 ? 'bg-yellow-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${utilizationPercent}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Manager</span>
                          <span className="font-medium">{warehouse.manager || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Phone</span>
                          <span className="font-medium">{warehouse.phone || 'N/A'}</span>
                        </div>
                      </div>
                      <button 
                        onClick={() => { setSelectedWarehouse(warehouse); setShowWarehouseModal(true); }}
                        className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium"
                      >
                        Manage Warehouse
                      </button>
                    </div>
                  );
                }) : (
                  <div className="col-span-3 text-center py-12 text-gray-500">
                    <p className="text-lg">No warehouses found</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'orders' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-4 border-b border-gray-200 bg-gray-50">
                <h3 className="text-lg font-bold text-gray-900">📦 Order Management</h3>
                <p className="text-sm text-gray-600 mt-1">Manage and reassign orders with AI assistance</p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Driver</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Route</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cost</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {orders.map((order) => {
                      const driver = drivers.find(d => d.id === order.assigned_driver);
                      return (
                        <tr key={order.id} className="hover:bg-blue-50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div>
                              <div className="font-medium text-gray-900">{order.tracking_number || order.id.slice(0, 8)}</div>
                              <div className="text-xs text-gray-500">{order.package_description}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div>
                              <div className="font-medium text-gray-900">{order.sender_name}</div>
                              <div className="text-xs text-gray-500">{order.sender_phone}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-3 py-1 text-xs font-semibold rounded-full ${getStatusColor(order.status)}`}>
                              {order.status.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            {driver ? (
                              <div>
                                <div className="font-medium text-gray-900">{driver.name}</div>
                                <div className="text-xs text-gray-500">{driver.vehicle_type} • ⭐ {driver.rating}</div>
                              </div>
                            ) : (
                              <span className="text-gray-400 italic">Unassigned</span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            <div className="max-w-xs">
                              <div className="font-medium">{order.pickup_city} → {order.delivery_city}</div>
                              <div className="text-xs truncate">{order.pickup_address}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div>
                              <div className="font-bold text-gray-900">{order.total_cost || order.price} MAD</div>
                              <div className="text-xs text-gray-500">{order.service_type}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div className="flex flex-col gap-1">
                              {order.status !== 'delivered' && order.status !== 'cancelled' && (
                                <>
                                  <button
                                    onClick={() => handleAIReassign(order.id)}
                                    className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white px-3 py-1 rounded-md text-xs font-medium hover:from-purple-600 hover:to-indigo-700 transition-all shadow-sm"
                                  >
                                    🤖 AI Reassign
                                  </button>
                                  <button
                                    onClick={() => handleManualReassign(order.id)}
                                    className="bg-blue-500 text-white px-3 py-1 rounded-md text-xs font-medium hover:bg-blue-600 transition-colors"
                                  >
                                    👤 Manual
                                  </button>
                                  <button
                                    onClick={() => handleCancelOrder(order.id)}
                                    className="bg-red-500 text-white px-3 py-1 rounded-md text-xs font-medium hover:bg-red-600 transition-colors"
                                  >
                                    ✕ Cancel
                                  </button>
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'drivers' && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-4 border-b border-gray-200 bg-gray-50">
                <h3 className="text-lg font-bold text-gray-900">🚗 Driver Management</h3>
                <p className="text-sm text-gray-600 mt-1">Monitor and manage driver fleet</p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Driver</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vehicle</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">City</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Orders</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rating</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {drivers.map((driver) => (
                      <tr key={driver.id} className="hover:bg-blue-50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{driver.name}</div>
                            <div className="text-sm text-gray-500">{driver.phone}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-3 py-1 text-xs font-semibold rounded-full ${getStatusColor(driver.status)}`}>
                            {driver.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {driver.vehicle_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {driver.assigned_city}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {driver.current_orders?.length || 0} active
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="flex items-center">
                            <span className="text-yellow-400">⭐</span>
                            <span className="ml-1 font-medium text-gray-900">{driver.rating}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {driver.status !== 'suspended' ? (
                            <button
                              onClick={() => handleSuspendDriver(driver.id, true)}
                              className="bg-red-500 text-white px-3 py-1 rounded-md text-xs font-medium hover:bg-red-600 transition-colors"
                            >
                              🚫 Suspend
                            </button>
                          ) : (
                            <button
                              onClick={() => handleSuspendDriver(driver.id, false)}
                              className="bg-green-500 text-white px-3 py-1 rounded-md text-xs font-medium hover:bg-green-600 transition-colors"
                            >
                              ✅ Activate
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'analytics' && advancedAnalytics && (
            <div className="space-y-6">
              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <h3 className="text-lg font-bold text-gray-900 mb-4">📊 Driver Performance</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Driver</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Orders</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Completed</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Success Rate</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Time</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rating</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Earnings</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {advancedAnalytics.driver_performance?.map(perf => (
                        <tr key={perf.driver_id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{perf.name}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{perf.total_orders}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{perf.completed_orders}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                              perf.success_rate >= 90 ? 'bg-green-100 text-green-800' :
                              perf.success_rate >= 70 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {perf.success_rate.toFixed(1)}%
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{perf.avg_delivery_time} min</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">⭐ {perf.rating}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">{perf.earnings.toFixed(2)} MAD</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Driver Reassignment Modal */}
        {showReassignModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-blue-500 to-indigo-600">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-xl font-bold text-white">👤 Select Driver for Reassignment</h3>
                    <p className="text-blue-100 text-sm mt-1">AI-powered recommendations sorted by score</p>
                  </div>
                  <button onClick={() => setShowReassignModal(false)} className="text-white hover:text-gray-200 transition-colors">
                    <X size={24} />
                  </button>
                </div>
              </div>
              <div className="p-6">
                {driverRecommendations.length > 0 ? (
                  <div className="space-y-3">
                    {driverRecommendations.map((rec, index) => (
                      <div key={rec.driver_id} className={`border-2 rounded-lg p-4 transition-all hover:shadow-md ${
                        index === 0 ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-blue-300'
                      }`}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg ${
                              index === 0 ? 'bg-green-500 text-white' :
                              index === 1 ? 'bg-blue-500 text-white' :
                              index === 2 ? 'bg-purple-500 text-white' :
                              'bg-gray-300 text-gray-700'
                            }`}>
                              #{index + 1}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <h4 className="font-bold text-gray-900">{rec.name}</h4>
                                {index === 0 && <span className="text-xs bg-green-500 text-white px-2 py-0.5 rounded-full font-medium">Best Match</span>}
                              </div>
                              <div className="flex items-center gap-3 mt-1 text-sm text-gray-600">
                                <span>🚗 {rec.vehicle_type}</span>
                                <span>⭐ {rec.rating}</span>
                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                  rec.status === 'available' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                                }`}>
                                  {rec.status}
                                </span>
                                <span>{rec.current_orders} orders</span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="text-right">
                              <div className="text-2xl font-bold text-blue-600">{rec.score}</div>
                              <div className="text-xs text-gray-500">AI Score</div>
                            </div>
                            <button
                              onClick={() => confirmManualReassign(rec.driver_id)}
                              disabled={!rec.available}
                              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                                rec.available
                                  ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg'
                                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                              }`}
                            >
                              {rec.available ? 'Assign' : 'Busy'}
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Loader className="animate-spin mx-auto mb-4" size={48} />
                    <p className="text-gray-500">Loading driver recommendations...</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Warehouse Management Modal */}
        {showWarehouseModal && selectedWarehouse && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-gray-200 bg-gradient-to-r from-purple-500 to-indigo-600">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-xl font-bold text-white">🏪 {selectedWarehouse.name}</h3>
                    <p className="text-purple-100 text-sm mt-1">{selectedWarehouse.city}</p>
                  </div>
                  <button onClick={() => setShowWarehouseModal(false)} className="text-white hover:text-gray-200 transition-colors">
                    <X size={24} />
                  </button>
                </div>
              </div>
              <div className="p-6 space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <label className="text-sm font-medium text-gray-700">City</label>
                    <p className="text-lg font-semibold text-gray-900 mt-1">{selectedWarehouse.city}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <label className="text-sm font-medium text-gray-700">Status</label>
                    <p className={`text-lg font-semibold mt-1 ${
                      selectedWarehouse.status === 'operational' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {selectedWarehouse.status}
                    </p>
                  </div>
                  <div className="col-span-2 bg-gray-50 p-4 rounded-lg">
                    <label className="text-sm font-medium text-gray-700">Address</label>
                    <p className="text-gray-900 mt-1">{selectedWarehouse.address}</p>
                  </div>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <label className="text-sm font-medium text-blue-700">Current Packages</label>
                    <p className="text-2xl font-bold text-blue-900 mt-1">{selectedWarehouse.current_packages || 0}</p>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <label className="text-sm font-medium text-purple-700">Capacity</label>
                    <p className="text-2xl font-bold text-purple-900 mt-1">{selectedWarehouse.capacity}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <label className="text-sm font-medium text-gray-700">Manager</label>
                    <p className="text-gray-900 mt-1">{selectedWarehouse.manager || 'N/A'}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <label className="text-sm font-medium text-gray-700">Phone</label>
                    <p className="text-gray-900 mt-1">{selectedWarehouse.phone || 'N/A'}</p>
                  </div>
                </div>
                
                {/* Utilization Bar */}
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="font-medium text-gray-700">Utilization</span>
                    <span className="font-bold text-gray-900">
                      {((selectedWarehouse.current_packages / selectedWarehouse.capacity) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className={`h-3 rounded-full transition-all ${
                        (selectedWarehouse.current_packages / selectedWarehouse.capacity) > 0.8 ? 'bg-red-500' : 
                        (selectedWarehouse.current_packages / selectedWarehouse.capacity) > 0.5 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${(selectedWarehouse.current_packages / selectedWarehouse.capacity) * 100}%` }}
                    />
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-200">
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <TrendingUp size={20} />
                    Quick Actions
                  </h4>
                  <div className="grid grid-cols-2 gap-3">
                    <button 
                      onClick={() => handleUpdateWarehouse(selectedWarehouse.id, 'operational')}
                      disabled={selectedWarehouse.status === 'operational'}
                      className="bg-green-600 hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-4 py-3 rounded-lg text-sm font-medium transition-colors shadow-md hover:shadow-lg"
                    >
                      ✅ Mark Operational
                    </button>
                    <button 
                      onClick={() => handleUpdateWarehouse(selectedWarehouse.id, 'closed')}
                      disabled={selectedWarehouse.status === 'closed'}
                      className="bg-red-600 hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white px-4 py-3 rounded-lg text-sm font-medium transition-colors shadow-md hover:shadow-lg"
                    >
                      🚫 Mark Closed
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
