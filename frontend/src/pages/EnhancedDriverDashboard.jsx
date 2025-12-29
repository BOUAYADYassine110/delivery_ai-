import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

const EnhancedDriverDashboard = () => {
  const [driver, setDriver] = useState(null);
  const [orders, setOrders] = useState([]);
  const [pendingAssignments, setPendingAssignments] = useState([]);
  const [earnings, setEarnings] = useState({});
  const [currentLocation, setCurrentLocation] = useState(null);
  const [isOnline, setIsOnline] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [showEmergency, setShowEmergency] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    const driverId = localStorage.getItem('driver_id') || 'DRV001';
    fetchDriverData(driverId);
    fetchEarnings(driverId);
    startLocationTracking();
    
    const interval = setInterval(() => {
      fetchDriverData(driverId);
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchDriverData = async (driverId) => {
    try {
      const response = await api.getDriverDashboard(driverId);
      setDriver(response.data.driver);
      setOrders(response.data.orders || []);
      setPendingAssignments(response.data.pending_assignments || []);
      setIsOnline(response.data.driver?.status === 'online' || response.data.driver?.status === 'busy');
    } catch (error) {
      console.error('Error fetching driver data:', error);
    }
  };

  const fetchEarnings = async (driverId) => {
    try {
      const response = await api.get(`/driver/${driverId}/earnings`);
      setEarnings(response.data);
    } catch (error) {
      console.error('Error fetching earnings:', error);
    }
  };

  const startLocationTracking = () => {
    if (navigator.geolocation) {
      navigator.geolocation.watchPosition(
        (position) => {
          const location = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          };
          setCurrentLocation(location);
          updateDriverLocation(location);
        },
        (error) => console.error('GPS Error:', error),
        { enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 }
      );
    }
  };

  const updateDriverLocation = async (location) => {
    const driverId = localStorage.getItem('driver_id') || 'DRV001';
    try {
      await api.post('/driver/gps/update', {
        driver_id: driverId,
        order_id: orders.find(o => o.status === 'in_transit')?.id,
        latitude: location.latitude,
        longitude: location.longitude,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('Error updating GPS:', error);
    }
  };

  const toggleOnlineStatus = async () => {
    const driverId = localStorage.getItem('driver_id') || 'DRV001';
    const newStatus = isOnline ? 'offline' : 'online';
    
    try {
      await api.post('/driver/status/update', {
        driver_id: driverId,
        status: newStatus,
        location: currentLocation
      });
      setIsOnline(!isOnline);
      fetchDriverData(driverId);
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  const handleAssignmentResponse = async (orderId, accept, reason = '') => {
    const driverId = localStorage.getItem('driver_id') || 'DRV001';
    try {
      await api.respondToAssignment({
        driver_id: driverId,
        order_id: orderId,
        accept,
        reason
      });
      fetchDriverData(driverId);
    } catch (error) {
      console.error('Error responding to assignment:', error);
    }
  };

  const startDelivery = async (orderId) => {
    const driverId = localStorage.getItem('driver_id') || 'DRV001';
    try {
      await api.startDeliveryRoute(orderId, { driver_id: driverId });
      fetchDriverData(driverId);
    } catch (error) {
      console.error('Error starting delivery:', error);
    }
  };

  const completeDelivery = async (orderId) => {
    const driverId = localStorage.getItem('driver_id') || 'DRV001';
    
    // Simulate proof of delivery
    const proofData = {
      order_id: orderId,
      driver_id: driverId,
      photo: 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...', // Mock base64 image
      signature: 'customer_signature',
      notes: 'Package delivered successfully',
      delivery_time: new Date().toISOString()
    };
    
    try {
      await api.post('/driver/proof-of-delivery', proofData);
      fetchDriverData(driverId);
      fetchEarnings(driverId);
    } catch (error) {
      console.error('Error completing delivery:', error);
    }
  };

  const sendEmergencyAlert = async (type, message) => {
    const driverId = localStorage.getItem('driver_id') || 'DRV001';
    try {
      await api.post('/driver/emergency', {
        driver_id: driverId,
        type,
        location: currentLocation,
        message
      });
      setShowEmergency(false);
      alert('Emergency alert sent to admin!');
    } catch (error) {
      console.error('Error sending emergency alert:', error);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending_acceptance': 'bg-yellow-100 text-yellow-800',
      'accepted': 'bg-blue-100 text-blue-800',
      'picked_up': 'bg-purple-100 text-purple-800',
      'in_transit': 'bg-indigo-100 text-indigo-800',
      'delivered': 'bg-green-100 text-green-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (!driver) {
    return (
      <div className="flex justify-center items-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading driver dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-4 h-4 rounded-full ${isOnline ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                <h1 className="text-xl font-bold text-gray-900">
                  {driver.name} - {driver.vehicle_type}
                </h1>
              </div>
              <button
                onClick={toggleOnlineStatus}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  isOnline 
                    ? 'bg-red-100 text-red-800 hover:bg-red-200' 
                    : 'bg-green-100 text-green-800 hover:bg-green-200'
                }`}
              >
                {isOnline ? '🔴 Go Offline' : '🟢 Go Online'}
              </button>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowEmergency(true)}
                className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700"
              >
                🚨 Emergency
              </button>
              <div className="text-sm text-gray-500">
                ⭐ {driver.rating} • {driver.total_deliveries} deliveries
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Today's Earnings</h3>
            <p className="text-2xl font-bold text-green-600">{earnings.today_earnings || 0} MAD</p>
            <p className="text-xs text-gray-500">{earnings.today_deliveries || 0} deliveries</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Total Earnings</h3>
            <p className="text-2xl font-bold text-blue-600">{earnings.total_earnings || 0} MAD</p>
            <p className="text-xs text-gray-500">{earnings.total_deliveries || 0} total</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Active Orders</h3>
            <p className="text-2xl font-bold text-purple-600">{orders.length}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">GPS Status</h3>
            <p className="text-2xl font-bold text-green-600">
              {currentLocation ? '🟢' : '🔴'}
            </p>
            <p className="text-xs text-gray-500">
              {currentLocation ? 'Active' : 'Inactive'}
            </p>
          </div>
        </div>

        {/* Pending Assignments */}
        {pendingAssignments.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold text-yellow-800 mb-4">
              🔔 New Assignment Requests ({pendingAssignments.length})
            </h2>
            {pendingAssignments.map((order) => (
              <div key={order.id} className="bg-white rounded-lg p-4 mb-4 border">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="font-medium text-gray-900">{order.tracking_number || order.id}</h3>
                      {order.service_type === 'express' && (
                        <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">
                          ⚡ Express
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium text-gray-700">📦 Pickup</p>
                        <p className="text-sm text-gray-600">{order.pickup_address}</p>
                        <p className="text-xs text-gray-500">{order.sender_name || 'Sender'}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-700">🏠 Delivery</p>
                        <p className="text-sm text-gray-600">{order.delivery_address}</p>
                        <p className="text-xs text-gray-500">{order.receiver_name || 'Receiver'}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                      <span>💰 {order.total_cost || order.price} MAD</span>
                      <span>📏 {order.weight || 1} kg</span>
                      <span>📦 {order.package_description || 'Package'}</span>
                    </div>
                  </div>
                  <div className="flex flex-col space-y-2 ml-4">
                    <button
                      onClick={() => handleAssignmentResponse(order.id, true)}
                      className="bg-green-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-600 flex items-center space-x-1"
                    >
                      <span>✅</span>
                      <span>Accept</span>
                    </button>
                    <button
                      onClick={() => handleAssignmentResponse(order.id, false, 'Not available')}
                      className="bg-red-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-600 flex items-center space-x-1"
                    >
                      <span>❌</span>
                      <span>Decline</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Current Orders */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              📋 My Orders ({orders.length})
            </h2>
          </div>
          <div className="p-6">
            {orders.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📦</div>
                <p className="text-gray-500 text-lg">No active orders</p>
                <p className="text-gray-400 text-sm">
                  {isOnline ? 'Waiting for new assignments...' : 'Go online to receive orders'}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {orders.map((order, index) => (
                  <div key={order.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center space-x-3">
                        <span className="bg-blue-100 text-blue-800 text-sm font-medium px-3 py-1 rounded-full">
                          #{index + 1}
                        </span>
                        <div>
                          <h3 className="font-medium text-gray-900">{order.tracking_number || order.id}</h3>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(order.status)}`}>
                            {order.status.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">{order.total_cost || order.price} MAD</p>
                        <p className="text-xs text-gray-500">{order.service_type}</p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <p className="text-sm font-medium text-gray-700">📦 Pickup</p>
                        <p className="text-sm text-gray-600">{order.pickup_address}</p>
                        <p className="text-xs text-gray-500">
                          {order.sender_name || 'Sender'} • {order.sender_phone || '+212661234567'}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-700">🏠 Delivery</p>
                        <p className="text-sm text-gray-600">{order.delivery_address}</p>
                        <p className="text-xs text-gray-500">
                          {order.receiver_name || 'Receiver'} • {order.receiver_phone || '+212667654321'}
                        </p>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {order.status === 'accepted' && (
                        <button
                          onClick={() => startDelivery(order.id)}
                          className="bg-blue-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-600 flex items-center space-x-1"
                        >
                          <span>🚀</span>
                          <span>Start Pickup</span>
                        </button>
                      )}
                      {order.status === 'picked_up' && (
                        <button
                          onClick={() => startDelivery(order.id)}
                          className="bg-purple-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-purple-600 flex items-center space-x-1"
                        >
                          <span>🚚</span>
                          <span>Start Delivery</span>
                        </button>
                      )}
                      {order.status === 'in_transit' && (
                        <button
                          onClick={() => completeDelivery(order.id)}
                          className="bg-green-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-600 flex items-center space-x-1"
                        >
                          <span>✅</span>
                          <span>Complete Delivery</span>
                        </button>
                      )}
                      <button
                        onClick={() => window.open(`https://maps.google.com/maps?q=${order.pickup_address || order.delivery_address}`, '_blank')}
                        className="bg-gray-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-600 flex items-center space-x-1"
                      >
                        <span>🗺️</span>
                        <span>Navigate</span>
                      </button>
                      <button
                        onClick={() => window.open(`tel:${order.status === 'accepted' ? order.sender_phone : order.receiver_phone}`, '_self')}
                        className="bg-yellow-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-yellow-600 flex items-center space-x-1"
                      >
                        <span>📞</span>
                        <span>Call</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Current Location */}
        {currentLocation && (
          <div className="bg-white rounded-lg shadow p-6 mt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">📍 Current Location</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-600">Latitude</p>
                <p className="text-sm font-medium">{currentLocation.latitude.toFixed(6)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Longitude</p>
                <p className="text-sm font-medium">{currentLocation.longitude.toFixed(6)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Accuracy</p>
                <p className="text-sm font-medium">{currentLocation.accuracy?.toFixed(0) || 'N/A'} m</p>
              </div>
            </div>
            <button
              onClick={() => window.open(`https://maps.google.com/maps?q=${currentLocation.latitude},${currentLocation.longitude}`, '_blank')}
              className="mt-4 bg-blue-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-600"
            >
              🗺️ View on Map
            </button>
          </div>
        )}
      </div>

      {/* Emergency Modal */}
      {showEmergency && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-red-800 mb-4">🚨 Emergency Alert</h3>
            <div className="space-y-3">
              <button
                onClick={() => sendEmergencyAlert('panic', 'Driver needs immediate assistance')}
                className="w-full bg-red-600 text-white py-3 px-4 rounded-lg hover:bg-red-700"
              >
                🆘 Panic Button
              </button>
              <button
                onClick={() => sendEmergencyAlert('breakdown', 'Vehicle breakdown - need assistance')}
                className="w-full bg-orange-600 text-white py-3 px-4 rounded-lg hover:bg-orange-700"
              >
                🔧 Vehicle Breakdown
              </button>
              <button
                onClick={() => sendEmergencyAlert('accident', 'Traffic accident - need help')}
                className="w-full bg-yellow-600 text-white py-3 px-4 rounded-lg hover:bg-yellow-700"
              >
                🚗 Traffic Accident
              </button>
              <button
                onClick={() => setShowEmergency(false)}
                className="w-full bg-gray-300 text-gray-700 py-3 px-4 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedDriverDashboard;