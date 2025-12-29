import { useQuery } from 'react-query'
import { api } from '../services/api'
import { Activity, CheckCircle, Zap, TrendingUp } from 'lucide-react'

export default function AgentMonitor() {
  const { data, isLoading } = useQuery('agents', () => api.getAgentStatus().then(res => res.data))

  return (
    <div className="animate-fade-in">
      <div className="flex items-center gap-3 mb-8">
        <Activity className="w-8 h-8 text-blue-600" />
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">Agent Monitor</h1>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data?.agents?.map((agent, idx) => (
            <div key={agent.name} className="group bg-white rounded-2xl shadow-lg p-6 border border-gray-100 hover:shadow-2xl hover:scale-105 transition-all duration-300 animate-fade-in" style={{ animationDelay: `${idx * 0.1}s` }}>
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-bold text-lg text-gray-800 mb-2">{agent.name}</h3>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span className="text-sm font-semibold text-green-600 uppercase tracking-wide">{agent.status}</span>
                  </div>
                </div>
                <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-3 rounded-xl group-hover:rotate-12 transition-transform shadow-lg">
                  <Zap className="w-6 h-6 text-white" />
                </div>
              </div>
              
              <div className="mt-6 pt-4 border-t border-gray-200">
                <div className="flex justify-between items-center mb-3">
                  <span className="text-gray-600 font-medium">Active Tasks</span>
                  <span className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">{agent.tasks}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-indigo-600 h-3 rounded-full transition-all duration-1000 shadow-lg" 
                    style={{ width: `${Math.min(agent.tasks * 10, 100)}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 bg-gradient-to-r from-blue-500 via-indigo-600 to-purple-600 rounded-2xl shadow-2xl p-8 text-white">
        <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <TrendingUp className="w-6 h-6" />
          System Overview
        </h2>
        <div className="grid grid-cols-3 gap-8">
          <div className="text-center group cursor-pointer">
            <p className="text-5xl font-bold mb-2 group-hover:scale-125 transition-transform">{data?.agents?.filter(a => a.status === 'active').length || 0}</p>
            <p className="text-blue-100 font-medium">Active Agents</p>
          </div>
          <div className="text-center group cursor-pointer">
            <p className="text-5xl font-bold mb-2 group-hover:scale-125 transition-transform">
              {data?.agents?.reduce((sum, a) => sum + a.tasks, 0) || 0}
            </p>
            <p className="text-blue-100 font-medium">Total Tasks</p>
          </div>
          <div className="text-center group cursor-pointer">
            <p className="text-5xl font-bold mb-2 group-hover:scale-125 transition-transform">100%</p>
            <p className="text-blue-100 font-medium">System Health</p>
          </div>
        </div>
      </div>
    </div>
  )
}
