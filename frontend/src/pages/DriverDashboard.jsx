import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import LiveGPSTracker from '../components/LiveGPSTracker';
import AdvancedRouteDisplay from '../components/RouteMapDisplay';
import MultiPackageManager from '../components/MultiPackageManager';

const DriverDashboard = () => {
  const [driver, setDriver] = useState(null);
  const [orders, setOrders] = useState([]);
  const [pendingAssignments, setPendingAssignments] = useState([]);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [isTracking, setIsTracking] = useState(false);
  const [earnings, setEarnings] = useState({});
  const [isOnline, setIsOnline] = useState(false);
  const [showEmergency, setShowEmergency] = useState(false);

  useEffect(() => {
    const driverId = localStorage.getItem('driver_id') || 'DRV001';
    fetchDriverData(driverId);
    fetchEarnings(driverId);
    startLocationTracking();
  }, []);
  
  const fetchEarnings = async (driverId) => {
    try {
      const response = await api.get(`/driver/${driverId}/earnings`);
      setEarnings(response.data);
    } catch (error) {
      console.log('Earnings endpoint not available yet');
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
      console.log('Status update not available yet');
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
      console.log('Emergency system not available yet');
    }
  };

  const fetchDriverData = async (driverId) => {
    try {
      const response = await api.getDriverDashboard(driverId);
      console.log('Driver data:', response.data);
      setDriver(response.data.driver);
      setOrders(response.data.orders || []);
      setPendingAssignments(response.data.pending_assignments || []);
    } catch (error) {
      console.error('Error fetching driver data:', error);
      // Set fallback data
      setDriver({
        id: driverId,
        name: 'Test Driver',
        vehicle_type: 'bike',
        rating: 4.5,
        status: 'available'
      });
      setOrders([]);
      setPendingAssignments([]);
    }
  };

  const startLocationTracking = () => {
    if (navigator.geolocation) {
      setIsTracking(true);
      navigator.geolocation.watchPosition(
        (position) => {
          const location = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          };
          setCurrentLocation(location);
          updateGPSLocation(location);
        },
        (error) => console.error('GPS Error:', error),
        { enableHighAccuracy: true, maximumAge: 10000, timeout: 5000 }
      );
    }
  };

  const updateDriverStatus = async (newStatus) => {
    const driverId = localStorage.getItem('driver_id') || 'DRV001';
    try {
      await fetch('http://localhost:8001/api/driver/status/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          driver_id: driverId,
          status: newStatus,
          location: currentLocation
        })
      });
      setDriver(prev => ({ ...prev, status: newStatus }));
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  const updateGPSLocation = async (location) => {
    const driverId = localStorage.getItem('driver_id') || 'DRV001';
    const activeOrder = orders.find(o => o.status === 'in_transit');
    
    if (activeOrder) {
      try {
        await api.post('/driver/gps/update', {
          driver_id: driverId,
          order_id: activeOrder.id,
          latitude: location.latitude,
          longitude: location.longitude,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        console.error('Error updating GPS:', error);
      }
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
      
      // Refresh data
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

  const completeDelivery = async (orderId, notes = '', proofPhoto = '') => {
    const driverId = localStorage.getItem('driver_id') || 'DRV001';
    try {
      await api.completeDeliveryFinal({
        order_id: orderId,
        driver_id: driverId,
        notes,
        proof_photo: proofPhoto
      });
      fetchDriverData(driverId);
    } catch (error) {
      console.error('Error completing delivery:', error);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending_acceptance': 'bg-yellow-100 text-yellow-800',
      'accepted': 'bg-blue-100 text-blue-800',
      'in_transit': 'bg-purple-100 text-purple-800',
      'delivered': 'bg-green-100 text-green-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (!driver) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  // Route Display Component
  const RouteDisplay = ({ driverId, orders }) => {
    const [route, setRoute] = useState(null);
    
    useEffect(() => {
      const fetchRoute = async () => {
        try {
          const response = await api.getDriverRoute(driverId);
          setRoute(response.data.route);
        } catch (error) {
          console.error('Error fetching route:', error);
        }
      };
      
      if (orders.length > 0) {
        fetchRoute();
      }
    }, [driverId, orders]);
    
    if (!route || !route.route_points || route.route_points.length === 0) {
      return <p className="text-gray-500">No route available</p>;
    }
    
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-sm text-gray-600">Total Distance: <span className="font-medium">{route.total_distance} km</span></p>
            <p className="text-sm text-gray-600">Estimated Time: <span className="font-medium">{route.estimated_time} min</span></p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Stops: <span className="font-medium">{route.total_stops}</span></p>
            <p className="text-sm text-gray-600">Efficiency: <span className="font-medium text-green-600">{route.route_efficiency}</span></p>
          </div>
        </div>
        
        <div className="space-y-3">
          {route.route_points.map((point, index) => (
            <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
              <div className="flex-shrink-0">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${
                  point.type === 'start' ? 'bg-blue-500' :
                  point.type === 'pickup' ? 'bg-orange-500' :
                  point.type === 'delivery' ? 'bg-green-500' : 'bg-gray-500'
                }`}>
                  {index + 1}
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-900">
                    {point.type === 'start' ? '🏁 Start' :
                     point.type === 'pickup' ? '📦 Pickup' :
                     point.type === 'delivery' ? '🏠 Delivery' : point.type}
                  </span>
                  {point.priority === 1 && (
                    <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">Express</span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">{point.address}</p>
                {point.contact_name && (
                  <p className="text-xs text-gray-500">{point.contact_name} • {point.contact_phone}</p>
                )}
                <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                  <span>📍 {point.distance_from_previous} km</span>
                  <span>⏱️ {new Date(point.estimated_arrival).toLocaleTimeString()}</span>
                  {point.estimated_duration && <span>⏳ {point.estimated_duration} min</span>}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };
  
  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Enhanced Driver Header */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Welcome, {driver.name}</h1>
                <div className="flex items-center space-x-4 mt-1">
                  <p className="text-gray-600">{driver.vehicle_type} • Rating: ⭐ {driver.rating}</p>
                  {driver.assigned_city && (
                    <span className="bg-blue-100 text-blue-800 text-sm px-3 py-1 rounded-full font-medium">
                      📍 {driver.assigned_city}
                    </span>
                  )}
                  {driver.specialties && driver.specialties.length > 0 && (
                    <div className="flex space-x-1">
                      {driver.specialties.slice(0, 2).map((specialty, index) => (
                        <span key={index} className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                          {specialty.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
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
            <div className="text-right">
              <div className="flex items-center space-x-2 mb-2">
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                  driver.status === 'available' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {driver.status}
                </div>
                <button
                  onClick={() => setShowEmergency(true)}
                  className="bg-red-600 text-white px-3 py-1 rounded-lg text-sm hover:bg-red-700"
                >
                  🚨 Emergency
                </button>
              </div>
              <p className="text-sm text-gray-500">
                GPS: {isTracking ? '🟢 Active' : '🔴 Inactive'}
              </p>
              <p className="text-sm text-gray-500">
                Today: {earnings.today_earnings || 0} MAD
              </p>
              {driver.working_hours && (
                <p className="text-xs text-gray-400">
                  Hours: {driver.working_hours.start} - {driver.working_hours.end}
                </p>
              )}
            </div>
          </div>
        </div>
        
        {/* Earnings Summary */}
        {earnings.total_earnings && (
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
              <h3 className="text-sm font-medium text-gray-500">Commission Rate</h3>
              <p className="text-2xl font-bold text-purple-600">{earnings.commission_rate || 15}%</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Active Orders</h3>
              <p className="text-2xl font-bold text-orange-600">{orders.length}</p>
            </div>
          </div>
        )}

        {/* Pending Assignments */}
        {pendingAssignments.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold text-yellow-800 mb-4">New Assignment Requests</h2>
            {pendingAssignments.map((order) => (
              <div key={order.id} className="bg-white rounded-lg p-4 mb-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-gray-900">{order.tracking_number}</h3>
                    <p className="text-sm text-gray-600">
                      {order.pickup_address} → {order.delivery_address}
                    </p>
                    <p className="text-sm text-gray-500">Cost: {order.total_cost} MAD</p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleAssignmentResponse(order.id, true)}
                      className="bg-green-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-600"
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => handleAssignmentResponse(order.id, false, 'Not available')}
                      className="bg-red-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-600"
                    >
                      Decline
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Multi-Package Manager */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">📦 Multi-Package Optimization</h2>
            <p className="text-sm text-gray-600">Manage multiple deliveries with cost and time optimization</p>
          </div>
          <div className="p-6">
            <MultiPackageManager driverId={driver.id} />
          </div>
        </div>

        {/* Advanced Route Navigation */}
        {orders.length > 0 && (
          <div className="bg-white rounded-lg shadow mb-6" data-route-section>
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">🗺️ Advanced Route Navigation</h2>
              <p className="text-sm text-gray-600">Best route selection with turn-by-turn navigation</p>
            </div>
            <div className="p-6">
              <AdvancedRouteDisplay 
                driverLocation={currentLocation ? {
                  lat: currentLocation.latitude,
                  lng: currentLocation.longitude
                } : {
                  lat: driver.current_location?.lat || 33.5731,
                  lng: driver.current_location?.lng || -7.5898
                }}
                destinations={orders.map(order => {
                  const cityCoords = {
                    'casablanca': { lat: 33.5731, lng: -7.5898 },
                    'rabat': { lat: 34.0209, lng: -6.8416 },
                    'marrakech': { lat: 31.6295, lng: -7.9811 },
                    'el jadida': { lat: 33.2316, lng: -8.5007 },
                    'salé': { lat: 34.0531, lng: -6.7985 },
                    'agadir': { lat: 30.4278, lng: -9.5981 }
                  };
                  
                  const city = order.delivery_city?.toLowerCase() || 'casablanca';
                  const coords = cityCoords[city] || cityCoords['casablanca'];
                  
                  return {
                    id: order.id,
                    lat: coords.lat + (Math.random() - 0.5) * 0.02,
                    lng: coords.lng + (Math.random() - 0.5) * 0.02,
                    address: order.delivery_address,
                    city: order.delivery_city,
                    type: 'delivery'
                  };
                })}
                onRouteSelect={(route) => {
                  console.log('Selected route:', route);
                }}
              />
            </div>
          </div>
        )}

        {/* Current Orders */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">My Orders ({orders.length})</h2>
          </div>
          <div className="p-6">
            {orders.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No active orders</p>
            ) : (
              <div className="space-y-4">
                {orders.map((order, index) => (
                  <div key={order.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded-full">
                            #{index + 1}
                          </span>
                          <h3 className="font-medium text-gray-900">{order.tracking_number || order.id}</h3>
                        </div>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(order.status)} mt-1 inline-block`}>
                          {order.status.replace('_', ' ')}
                        </span>
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
                        <p className="text-xs text-gray-500">{order.sender_name || 'Sender'} • {order.sender_phone || '+212661234567'}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-700">🏠 Delivery</p>
                        <p className="text-sm text-gray-600">{order.delivery_address}</p>
                        <p className="text-xs text-gray-500">{order.receiver_name || 'Receiver'} • {order.receiver_phone || '+212667654321'}</p>
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
                          onClick={() => completeDelivery(order.id, 'Delivered successfully')}
                          className="bg-green-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-600 flex items-center space-x-1"
                        >
                          <span>✅</span>
                          <span>Complete Delivery</span>
                        </button>
                      )}
                      <button
                        onClick={() => {
                          // Use in-app navigation instead of Google Maps
                          const routeSection = document.querySelector('[data-route-section]');
                          if (routeSection) {
                            routeSection.scrollIntoView({ behavior: 'smooth' });
                          }
                        }}
                        className="bg-blue-500 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-600 flex items-center space-x-1"
                      >
                        <span>🗺️</span>
                        <span>View Route</span>
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

        {/* Driver Status Control */}
        <div className="bg-white rounded-lg shadow p-6 mt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Driver Status</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {['available', 'busy', 'break', 'offline'].map((status) => (
              <button
                key={status}
                onClick={() => updateDriverStatus(status)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  driver.status === status
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Live GPS Tracker */}
        <div className="mt-6">
          <LiveGPSTracker 
            orderId={orders.find(o => o.status === 'in_transit')?.id}
            pickupCoords={orders.find(o => o.status === 'accepted') ? {
              lat: driver.current_location?.lat || 33.5731,
              lng: driver.current_location?.lng || -7.5898
            } : null}
            deliveryCoords={orders.find(o => o.status === 'in_transit') ? {
              lat: orders.find(o => o.status === 'in_transit')?.current_location?.lat || 33.5750,
              lng: orders.find(o => o.status === 'in_transit')?.current_location?.lng || -7.5900
            } : null}
            onLocationUpdate={(location) => {
              setCurrentLocation({
                latitude: location.lat,
                longitude: location.lng,
                accuracy: location.accuracy
              });
              updateGPSLocation({
                latitude: location.lat,
                longitude: location.lng
              });
            }}
          />
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
    </div>
  );
};

export default DriverDashboard;