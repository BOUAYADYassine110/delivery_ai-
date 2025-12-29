import React, { useState } from 'react';

const AssignmentSimulator = () => {
  const [simulation, setSimulation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [params, setParams] = useState({
    pickup_city: 'Casablanca',
    weight: 2.0,
    service_type: 'standard',
    fragile: false
  });

  const cities = ['Casablanca', 'Rabat', 'Marrakech', 'Agadir', 'El Jadida', 'Salé'];

  const runSimulation = async () => {
    setLoading(true);
    try {
      const queryParams = new URLSearchParams(params).toString();
      const response = await fetch(`http://localhost:8001/api/assignment/simulate?${queryParams}`);
      const data = await response.json();
      setSimulation(data);
    } catch (error) {
      console.error('Simulation error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-blue-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBar = (score) => {
    const percentage = Math.min(100, (score / 100) * 100);
    const color = score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-blue-500' : score >= 40 ? 'bg-yellow-500' : 'bg-red-500';
    
    return (
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div className={`${color} h-2 rounded-full transition-all duration-300`} style={{ width: `${percentage}%` }}></div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">🎯 Assignment Simulator</h2>
      <p className="text-gray-600 mb-6">Test the intelligent driver assignment algorithm with different parameters</p>

      {/* Simulation Parameters */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Pickup City</label>
          <select
            value={params.pickup_city}
            onChange={(e) => setParams({...params, pickup_city: e.target.value})}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {cities.map(city => (
              <option key={city} value={city}>{city}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Weight (kg)</label>
          <input
            type="number"
            value={params.weight}
            onChange={(e) => setParams({...params, weight: parseFloat(e.target.value)})}
            min="0.1"
            max="200"
            step="0.1"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Service Type</label>
          <select
            value={params.service_type}
            onChange={(e) => setParams({...params, service_type: e.target.value})}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="standard">Standard</option>
            <option value="express">Express</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Package Type</label>
          <div className="flex items-center space-x-4 pt-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={params.fragile}
                onChange={(e) => setParams({...params, fragile: e.target.checked})}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">Fragile</span>
            </label>
          </div>
        </div>
      </div>

      {/* Run Simulation Button */}
      <div className="mb-6">
        <button
          onClick={runSimulation}
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Running Simulation...</span>
            </>
          ) : (
            <>
              <span>🚀</span>
              <span>Run Assignment Simulation</span>
            </>
          )}
        </button>
      </div>

      {/* Simulation Results */}
      {simulation && (
        <div className="space-y-6">
          {/* Best Match */}
          {simulation.best_match && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-green-800 mb-4">🏆 Best Match Selected</h3>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-bold">
                      {simulation.best_match.driver.name.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{simulation.best_match.driver.name}</p>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm bg-gray-200 text-gray-700 px-2 py-1 rounded">
                        {simulation.best_match.driver.vehicle_type}
                      </span>
                      <span className="text-sm text-gray-600">
                        ⭐ {simulation.best_match.driver.rating}
                      </span>
                      <span className="text-sm text-gray-600">
                        📍 {simulation.best_match.distance_km} km away
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-2xl font-bold ${getScoreColor(simulation.best_match.score)}`}>
                    {simulation.best_match.score}
                  </p>
                  <p className="text-sm text-gray-500">Assignment Score</p>
                </div>
              </div>
            </div>
          )}

          {/* Selection Criteria */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-4">📊 Selection Criteria</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Object.entries(simulation.selection_criteria).map(([key, description]) => (
                <div key={key} className="flex items-center space-x-3">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <div>
                    <p className="font-medium text-gray-900 capitalize">{key.replace('_', ' ')}</p>
                    <p className="text-sm text-gray-600">{description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* All Driver Scores */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              📋 All Drivers in {simulation.city} ({simulation.available_drivers} available)
            </h3>
            <div className="space-y-4">
              {simulation.all_scores.map((item, index) => (
                <div key={item.driver.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold ${
                      index === 0 ? 'bg-green-500' : index === 1 ? 'bg-blue-500' : index === 2 ? 'bg-yellow-500' : 'bg-gray-500'
                    }`}>
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{item.driver.name}</p>
                      <div className="flex items-center space-x-2 text-sm text-gray-600">
                        <span>{item.driver.vehicle_type}</span>
                        <span>•</span>
                        <span>⭐ {item.driver.rating}</span>
                        <span>•</span>
                        <span>📍 {item.distance_km} km</span>
                        <span>•</span>
                        <span>{item.driver.current_orders} orders</span>
                      </div>
                      {item.driver.specialties.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {item.driver.specialties.map((specialty, idx) => (
                            <span key={idx} className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
                              {specialty.replace('_', ' ')}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-right min-w-[120px]">
                    <p className={`text-xl font-bold ${getScoreColor(item.score)}`}>
                      {item.score}
                    </p>
                    <div className="w-20 mt-1">
                      {getScoreBar(item.score)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Test Order Summary */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">📦 Test Order Details</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-700">Pickup City</p>
                <p className="text-lg text-gray-900">{simulation.test_order.pickup_city}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">Weight</p>
                <p className="text-lg text-gray-900">{simulation.test_order.weight} kg</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">Service Type</p>
                <p className="text-lg text-gray-900 capitalize">{simulation.test_order.service_type}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700">Special Requirements</p>
                <p className="text-lg text-gray-900">{simulation.test_order.fragile ? 'Fragile' : 'Standard'}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssignmentSimulator;