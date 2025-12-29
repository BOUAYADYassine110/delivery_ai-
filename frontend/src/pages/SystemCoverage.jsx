import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import AssignmentSimulator from '../components/AssignmentSimulator';

const SystemCoverage = () => {
  const [coverage, setCoverage] = useState(null);
  const [cityDrivers, setCityDrivers] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSystemCoverage();
    fetchDriversByCity();
  }, []);

  const fetchSystemCoverage = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/system/coverage');
      const data = await response.json();
      setCoverage(data);
    } catch (error) {
      console.error('Error fetching coverage:', error);
    }
  };

  const fetchDriversByCity = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/drivers/by-city');
      const data = await response.json();
      setCityDrivers(data.city_assignments);
    } catch (error) {
      console.error('Error fetching city drivers:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading system coverage...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">🚀 Ultimate System Coverage</h1>
              <p className="text-gray-600 mt-1">Multi-Agent Delivery System - Ultimate Version 3.0</p>
              <div className="flex items-center space-x-4 mt-2">
                <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                  {Object.values(cityDrivers).flat().length} Total Drivers
                </span>
                <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                  Multi-Driver Coverage
                </span>
                <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium">
                  AI-Powered Assignment
                </span>
              </div>
            </div>
            <div className="text-right">
              <div className="bg-green-100 text-green-800 px-4 py-2 rounded-lg">
                <span className="font-semibold">{coverage?.total_coverage || 0}/6</span> Cities Covered
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Avg: {coverage?.average_drivers_per_city || 0} drivers/city
              </p>
            </div>
          </div>
        </div>

        {/* Coverage Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-blue-100 text-blue-600">
                🏙️
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Cities</p>
                <p className="text-2xl font-bold text-gray-900">6</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100 text-green-600">
                🚗
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Drivers</p>
                <p className="text-2xl font-bold text-gray-900">{Object.values(cityDrivers).flat().length}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-purple-100 text-purple-600">
                🏪
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Warehouses</p>
                <p className="text-2xl font-bold text-gray-900">6</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-orange-100 text-orange-600">
                ✅
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Coverage</p>
                <p className="text-2xl font-bold text-gray-900">100%</p>
              </div>
            </div>
          </div>
        </div>

        {/* City Coverage Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
          {Object.entries(cityDrivers).map(([cityName, drivers]) => {
            const coverageLevel = drivers.length >= 3 ? 'excellent' : drivers.length >= 2 ? 'good' : drivers.length >= 1 ? 'basic' : 'none';
            const coverageColors = {
              excellent: 'from-green-500 to-green-600',
              good: 'from-blue-500 to-blue-600', 
              basic: 'from-yellow-500 to-yellow-600',
              none: 'from-red-500 to-red-600'
            };
            
            return (
              <div key={cityName} className="bg-white rounded-lg shadow overflow-hidden">
                <div className={`bg-gradient-to-r ${coverageColors[coverageLevel]} px-6 py-4`}>
                  <h3 className="text-xl font-bold text-white flex items-center justify-between">
                    <span>📍 {cityName}</span>
                    <span className="text-sm bg-white bg-opacity-20 px-2 py-1 rounded">
                      {drivers.length} drivers
                    </span>
                  </h3>
                  <p className="text-white text-opacity-90 text-sm">
                    Coverage: {coverageLevel.charAt(0).toUpperCase() + coverageLevel.slice(1)}
                  </p>
                </div>
                
                <div className="p-6">
                  {drivers.length === 0 ? (
                    <div className="text-center py-4">
                      <p className="text-gray-500">No drivers assigned</p>
                      <span className="inline-block mt-2 px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm">
                        No Coverage
                      </span>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {drivers.map((driver, index) => (
                        <div key={driver.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center">
                              <span className="text-white font-semibold text-sm">
                                {driver.name.split(' ').map(n => n[0]).join('')}
                              </span>
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">{driver.name}</p>
                              <div className="flex items-center space-x-2">
                                <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                                  {driver.vehicle_type}
                                </span>
                                <span className={`text-xs px-2 py-1 rounded ${
                                  driver.status === 'available' 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-orange-100 text-orange-800'
                                }`}>
                                  {driver.status}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-medium text-gray-900">⭐ {driver.rating}</p>
                            <p className="text-xs text-gray-500">{driver.current_orders} active</p>
                          </div>
                        </div>
                      ))}
                      
                      {/* Enhanced Driver Info */}
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="font-medium text-gray-700">Vehicle Types:</p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {[...new Set(drivers.map(d => d.vehicle_type))].map((type, index) => (
                                <span key={index} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                  {type}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div>
                            <p className="font-medium text-gray-700">Avg Rating:</p>
                            <p className="text-lg font-bold text-green-600">
                              {(drivers.reduce((sum, d) => sum + d.rating, 0) / drivers.length).toFixed(1)}
                            </p>
                          </div>
                        </div>
                        
                        <div className="mt-3">
                          <p className="font-medium text-gray-700 mb-2">Specialties:</p>
                          <div className="flex flex-wrap gap-1">
                            {[...new Set(drivers.flatMap(d => d.specialties || []))].map((specialty, index) => (
                              <span key={index} className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                                {specialty.replace('_', ' ')}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Vehicle Distribution */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">🚗 Vehicle Distribution</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {coverage?.vehicle_distribution && Object.entries(coverage.vehicle_distribution).map(([vehicle, count]) => (
              <div key={vehicle} className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl mb-2">
                  {vehicle === 'bike' ? '🚲' : 
                   vehicle === 'scooter' ? '🛵' : 
                   vehicle === 'car' ? '🚗' : 
                   vehicle === 'van' ? '🚐' : '🚚'}
                </div>
                <p className="font-medium text-gray-900 capitalize">{vehicle}</p>
                <p className="text-2xl font-bold text-blue-600">{count}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Assignment Simulator */}
        <div className="mb-6">
          <AssignmentSimulator />
        </div>

        {/* System Status */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">📊 System Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">✅</span>
              </div>
              <h3 className="font-semibold text-gray-900">Full Coverage</h3>
              <p className="text-sm text-gray-600">All 6 cities have assigned drivers</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">🏪</span>
              </div>
              <h3 className="font-semibold text-gray-900">Warehouse Network</h3>
              <p className="text-sm text-gray-600">Complete warehouse infrastructure</p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">🚀</span>
              </div>
              <h3 className="font-semibold text-gray-900">Ready for Operations</h3>
              <p className="text-sm text-gray-600">System fully operational</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemCoverage;