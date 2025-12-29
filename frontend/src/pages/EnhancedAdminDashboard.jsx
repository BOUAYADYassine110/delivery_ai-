import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

const EnhancedAdminDashboard = () => {
  const [orders, setOrders] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [orderTracking, setOrderTracking] = useState(null);
  const [driverPriority, setDriverPriority] = useState(null);
  const [activeTab, setActiveTab] = useState('orders');

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [ordersRes, driversRes, analyticsRes] = await Promise.all([
        api.getAdminOrders(),
        api.getAdminDrivers(),
        api.getAdminAnalytics()
      ]);
      setOrders(ordersRes.data.orders || []);
      setDrivers(driversRes.data.drivers || []);
      setAnalytics(analyticsRes.data || {});
    } catch (error) {
      console.error('Error fetching admin data:', error);
    }
  };

  const trackOrder = async (orderId) => {
    try {
      const response = await api.get(`/admin/order/${orderId}/track`);
      setOrderTracking(response.data);
      setSelectedOrder(orderId);
    } catch (error) {
      console.error('Error tracking order:', error);
    }
  };

  const getDriverPriority = async (orderId) => {
    try {
      const response = await api.get(`/admin/drivers/priority/${orderId}`);
      setDriverPriority(response.data);
    } catch (error) {
      console.error('Error getting driver priority:', error);
    }
  };

  const reassignOrder = async (orderId, driverId) => {
    try {
      await api.post(`/admin/reassign/${orderId}/${driverId}`);
      fetchData();
      setDriverPriority(null);
    } catch (error) {
      console.error('Error reassigning order:', error);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending_assignment': 'bg-yellow-100 text-yellow-800',
      'pending_acceptance': 'bg-orange-100 text-orange-800',
      'accepted': 'bg-blue-100 text-blue-800',
      'in_transit': 'bg-purple-100 text-purple-800',
      'delivered': 'bg-green-100 text-green-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Enhanced Admin Dashboard</h1>
        
        {/* Analytics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Total Orders</h3>
            <p className="text-2xl font-bold text-gray-900">{analytics.total_orders || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Pending</h3>
            <p className="text-2xl font-bold text-yellow-600">{analytics.pending_orders || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">In Progress</h3>
            <p className="text-2xl font-bold text-blue-600">{analytics.in_progress || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Completed</h3>
            <p className="text-2xl font-bold text-green-600">{analytics.completed || 0}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Active Drivers</h3>
            <p className="text-2xl font-bold text-purple-600">{analytics.active_drivers || 0}</p>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Orders List */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Orders Management</h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {orders.map((order) => (
                  <div key={order.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-medium text-gray-900">{order.tracking_number || order.id}</h3>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(order.status)}`}>
                          {order.status.replace('_', ' ')}
                        </span>
                        {order.rejection_count > 0 && (
                          <span className="ml-2 px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
                            {order.rejection_count} rejections
                          </span>
                        )}
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">{order.total_cost || order.price} MAD</p>
                        <p className="text-xs text-gray-500">{order.service_type}</p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <p className="text-sm font-medium text-gray-700">Customer</p>
                        <p className="text-sm text-gray-600">{order.sender_name}</p>
                        <p className="text-xs text-gray-500">{order.sender_phone}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-700">Driver</p>
                        {order.driver_info ? (
                          <div>
                            <p className="text-sm text-gray-600">{order.driver_info.name}</p>
                            <p className="text-xs text-gray-500">
                              {order.driver_info.vehicle_type} • ⭐ {order.driver_info.rating}
                            </p>
                          </div>
                        ) : (
                          <p className="text-sm text-gray-500">Unassigned</p>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => trackOrder(order.id)}
                        className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600"
                      >
                        📍 Track
                      </button>
                      <button
                        onClick={() => getDriverPriority(order.id)}
                        className="bg-purple-500 text-white px-3 py-1 rounded text-sm hover:bg-purple-600"
                      >
                        👥 Drivers
                      </button>
                      {order.status === 'pending_assignment' && (
                        <button
                          onClick={() => getDriverPriority(order.id)}
                          className="bg-orange-500 text-white px-3 py-1 rounded text-sm hover:bg-orange-600"
                        >
                          🔄 Reassign
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Panel */}
          <div className="space-y-6">
            {/* Order Tracking */}
            {orderTracking && (
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Order Tracking</h3>
                  <p className="text-sm text-gray-600">Order: {orderTracking.order.tracking_number}</p>
                </div>
                <div className="p-6">
                  <div className="mb-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-700">Progress</span>
                      <span className="text-sm text-gray-600">{orderTracking.progress_percentage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${orderTracking.progress_percentage}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h4 className="font-medium text-gray-900">Tracking Events</h4>
                    {orderTracking.tracking_events?.map((event, index) => (
                      <div key={index} className="flex items-start space-x-3">
                        <div className={`w-3 h-3 rounded-full mt-1 ${
                          event.status === 'success' ? 'bg-green-500' :
                          event.status === 'warning' ? 'bg-yellow-500' :
                          'bg-blue-500'
                        }`}></div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">{event.event}</p>
                          <p className="text-xs text-gray-500">{event.description}</p>
                          <p className="text-xs text-gray-400">
                            {new Date(event.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Driver Priority List */}
            {driverPriority && (
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Driver Priority List</h3>
                  <p className="text-sm text-gray-600">
                    {driverPriority.available_drivers} available of {driverPriority.total_drivers} drivers
                  </p>
                </div>
                <div className="p-6">
                  <div className="space-y-3">
                    {driverPriority.drivers.map((driver, index) => (
                      <div key={driver.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center space-x-3">
                          <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded-full">
                            #{index + 1}
                          </span>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{driver.name}</p>
                            <p className="text-xs text-gray-500">
                              {driver.vehicle_type} • ⭐ {driver.rating} • {driver.distance} km
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className={`text-sm font-medium ${getPriorityColor(driver.score)}`}>
                            {driver.score}
                          </span>
                          {driver.available && !driver.rejected && (
                            <button
                              onClick={() => reassignOrder(driverPriority.order_id, driver.id)}
                              className="bg-green-500 text-white px-2 py-1 rounded text-xs hover:bg-green-600"
                            >
                              Assign
                            </button>
                          )}
                          {driver.rejected && (
                            <span className="text-xs text-red-500">Rejected</span>
                          )}
                          {!driver.available && (
                            <span className="text-xs text-gray-500">Busy</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedAdminDashboard;