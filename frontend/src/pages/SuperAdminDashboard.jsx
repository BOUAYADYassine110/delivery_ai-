import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

const SuperAdminDashboard = () => {
  const [liveData, setLiveData] = useState({ drivers: [], orders: [] });
  const [analytics, setAnalytics] = useState({});
  const [emergencies, setEmergencies] = useState([]);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [activeTab, setActiveTab] = useState('live-map');

  useEffect(() => {
    fetchLiveData();
    fetchAnalytics();
    fetchEmergencies();
    
    const interval = setInterval(() => {
      fetchLiveData();
      fetchEmergencies();
    }, 3000); // Update every 3 seconds
    
    return () => clearInterval(interval);
  }, []);

  const fetchLiveData = async () => {
    try {
      const response = await api.get('/admin/live-map');
      setLiveData(response.data);
    } catch (error) {
      console.error('Error fetching live data:', error);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await api.get('/admin/analytics/advanced');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const fetchEmergencies = async () => {
    try {
      const response = await api.get('/admin/emergencies');
      setEmergencies(response.data.emergencies || []);
    } catch (error) {
      console.error('Error fetching emergencies:', error);
    }
  };

  const suspendDriver = async (driverId, suspend, reason = '') => {
    try {
      await api.post(`/admin/driver/${driverId}/suspend`, { suspend, reason });
      fetchLiveData();
      fetchAnalytics();
    } catch (error) {
      console.error('Error suspending driver:', error);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'online': 'bg-green-500',
      'busy': 'bg-blue-500',
      'offline': 'bg-gray-500',
      'suspended': 'bg-red-500'
    };
    return colors[status] || 'bg-gray-500';
  };

  const getOrderStatusColor = (status) => {
    const colors = {
      'pending_assignment': 'bg-yellow-100 text-yellow-800',
      'pending_acceptance': 'bg-orange-100 text-orange-800',
      'accepted': 'bg-blue-100 text-blue-800',
      'in_transit': 'bg-purple-100 text-purple-800',
      'delivered': 'bg-green-100 text-green-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">🚀 Super Admin Dashboard</h1>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                Last updated: {new Date(liveData.timestamp).toLocaleTimeString()}
              </div>
              {emergencies.length > 0 && (
                <div className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-medium">
                  🚨 {emergencies.length} Emergency{emergencies.length > 1 ? 'ies' : ''}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Emergency Alerts */}
        {emergencies.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-semibold text-red-800 mb-3">🚨 Active Emergencies</h3>
            <div className="space-y-2">
              {emergencies.map((emergency) => (
                <div key={emergency.id} className="bg-white p-3 rounded border-l-4 border-red-500">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-red-800">{emergency.type.toUpperCase()}</p>
                      <p className="text-sm text-gray-600">{emergency.message}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(emergency.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <button className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700">
                      Respond
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analytics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Total Revenue</h3>
            <p className="text-2xl font-bold text-green-600">
              {analytics.revenue?.total || 0} MAD
            </p>
            <p className="text-xs text-gray-500">
              Today: {analytics.revenue?.today || 0} MAD
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Fleet Status</h3>
            <div className="flex items-center space-x-2 mt-2">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-1"></div>
                <span className="text-sm">{analytics.fleet_status?.online_drivers || 0}</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-blue-500 rounded-full mr-1"></div>
                <span className="text-sm">{analytics.fleet_status?.busy_drivers || 0}</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-gray-500 rounded-full mr-1"></div>
                <span className="text-sm">{analytics.fleet_status?.offline_drivers || 0}</span>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Active Orders</h3>
            <p className="text-2xl font-bold text-blue-600">{liveData.orders.length}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Active Drivers</h3>
            <p className="text-2xl font-bold text-purple-600">{liveData.drivers.length}</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex">
              {['live-map', 'drivers', 'orders', 'performance'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-2 px-4 border-b-2 font-medium text-sm capitalize ${
                    activeTab === tab
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab.replace('-', ' ')}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {/* Live Map Tab */}
            {activeTab === 'live-map' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Drivers Map */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">🚗 Live Drivers ({liveData.drivers.length})</h3>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {liveData.drivers.map((driver) => (
                      <div key={driver.id} className="border rounded-lg p-3">
                        <div className="flex justify-between items-start">
                          <div className="flex items-center space-x-3">
                            <div className={`w-4 h-4 rounded-full ${getStatusColor(driver.status)}`}></div>
                            <div>
                              <p className="font-medium">{driver.name}</p>
                              <p className="text-sm text-gray-500">
                                {driver.vehicle_type} • ⭐ {driver.rating} • {driver.current_orders} orders
                              </p>
                              <p className="text-xs text-gray-400">
                                📍 {driver.location.lat.toFixed(4)}, {driver.location.lng.toFixed(4)}
                              </p>
                            </div>
                          </div>
                          <div className="flex space-x-1">
                            <button
                              onClick={() => setSelectedDriver(driver)}
                              className="bg-blue-500 text-white px-2 py-1 rounded text-xs hover:bg-blue-600"
                            >
                              View
                            </button>
                            <button
                              onClick={() => suspendDriver(driver.id, true, 'Admin action')}
                              className="bg-red-500 text-white px-2 py-1 rounded text-xs hover:bg-red-600"
                            >
                              Suspend
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Orders Map */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">📦 Active Orders ({liveData.orders.length})</h3>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {liveData.orders.map((order) => (
                      <div key={order.id} className="border rounded-lg p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium">{order.tracking_number}</p>
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getOrderStatusColor(order.status)}`}>
                              {order.status.replace('_', ' ')}
                            </span>
                            <p className="text-sm text-gray-500 mt-1">
                              📍 {order.pickup_location.lat.toFixed(4)}, {order.pickup_location.lng.toFixed(4)}
                            </p>
                            <p className="text-sm text-gray-500">
                              🎯 {order.delivery_location.lat.toFixed(4)}, {order.delivery_location.lng.toFixed(4)}
                            </p>
                            {order.assigned_driver && (
                              <p className="text-xs text-blue-600">
                                Driver: {liveData.drivers.find(d => d.id === order.assigned_driver)?.name || 'Unknown'}
                              </p>
                            )}
                          </div>
                          <div className="flex items-center">
                            {order.priority === 1 && (
                              <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">
                                Express
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Drivers Tab */}
            {activeTab === 'drivers' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Driver Management</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Driver</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Performance</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Earnings</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {analytics.driver_performance?.map((driver) => (
                        <tr key={driver.driver_id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">{driver.name}</div>
                              <div className="text-sm text-gray-500">⭐ {driver.rating}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className={`w-3 h-3 rounded-full mr-2 ${getStatusColor(
                                liveData.drivers.find(d => d.id === driver.driver_id)?.status || 'offline'
                              )}`}></div>
                              <span className="text-sm">
                                {liveData.drivers.find(d => d.id === driver.driver_id)?.status || 'offline'}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">
                              {driver.completed_orders}/{driver.total_orders} orders
                            </div>
                            <div className="text-sm text-gray-500">
                              {driver.success_rate.toFixed(1)}% success rate
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{driver.earnings.toFixed(2)} MAD</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button
                              onClick={() => suspendDriver(driver.driver_id, true)}
                              className="text-red-600 hover:text-red-900 mr-3"
                            >
                              Suspend
                            </button>
                            <button className="text-blue-600 hover:text-blue-900">
                              View Details
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Orders Tab */}
            {activeTab === 'orders' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Order Management</h3>
                <div className="space-y-4">
                  {liveData.orders.map((order) => (
                    <div key={order.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-medium">{order.tracking_number}</h4>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getOrderStatusColor(order.status)}`}>
                            {order.status.replace('_', ' ')}
                          </span>
                          <p className="text-sm text-gray-600 mt-2">
                            📍 Pickup: {order.pickup_location.lat.toFixed(4)}, {order.pickup_location.lng.toFixed(4)}
                          </p>
                          <p className="text-sm text-gray-600">
                            🎯 Delivery: {order.delivery_location.lat.toFixed(4)}, {order.delivery_location.lng.toFixed(4)}
                          </p>
                        </div>
                        <div className="flex space-x-2">
                          <button className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600">
                            Track
                          </button>
                          <button className="bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600">
                            Reassign
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Performance Tab */}
            {activeTab === 'performance' && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Performance Analytics</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-medium mb-3">Top Performers</h4>
                    {analytics.driver_performance?.slice(0, 5).map((driver, index) => (
                      <div key={driver.driver_id} className="flex justify-between items-center py-2">
                        <div className="flex items-center">
                          <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded-full mr-2">
                            #{index + 1}
                          </span>
                          <span className="text-sm">{driver.name}</span>
                        </div>
                        <span className="text-sm font-medium">⭐ {driver.rating}</span>
                      </div>
                    ))}
                  </div>
                  
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-medium mb-3">System Health</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm">Active Drivers</span>
                        <span className="text-sm font-medium text-green-600">
                          {analytics.fleet_status?.online_drivers + analytics.fleet_status?.busy_drivers || 0}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Orders in Progress</span>
                        <span className="text-sm font-medium text-blue-600">{liveData.orders.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Emergency Alerts</span>
                        <span className={`text-sm font-medium ${emergencies.length > 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {emergencies.length}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Driver Detail Modal */}
      {selectedDriver && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-semibold">Driver Details</h3>
              <button
                onClick={() => setSelectedDriver(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-700">Name</p>
                <p className="text-sm text-gray-900">{selectedDriver.name}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">Status</p>
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full mr-2 ${getStatusColor(selectedDriver.status)}`}></div>
                  <span className="text-sm">{selectedDriver.status}</span>
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">Vehicle</p>
                <p className="text-sm text-gray-900">{selectedDriver.vehicle_type}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">Current Orders</p>
                <p className="text-sm text-gray-900">{selectedDriver.current_orders}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">Rating</p>
                <p className="text-sm text-gray-900">⭐ {selectedDriver.rating}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">Location</p>
                <p className="text-sm text-gray-900">
                  {selectedDriver.location.lat.toFixed(4)}, {selectedDriver.location.lng.toFixed(4)}
                </p>
              </div>
            </div>
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => suspendDriver(selectedDriver.id, true, 'Admin review')}
                className="flex-1 bg-red-500 text-white py-2 px-4 rounded hover:bg-red-600"
              >
                Suspend
              </button>
              <button
                onClick={() => setSelectedDriver(null)}
                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SuperAdminDashboard;