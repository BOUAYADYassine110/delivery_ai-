import { useEffect, useState } from 'react'
import { Brain, CheckCircle, Loader, Sparkles, Zap } from 'lucide-react'

export default function AIProcessingModal({ isOpen, onClose, orderData }) {
  const [currentStep, setCurrentStep] = useState(0)
  const [completedSteps, setCompletedSteps] = useState([])

  const steps = [
    { 
      icon: Brain, 
      title: 'Analyzing Order', 
      description: 'AI is processing your delivery request',
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    { 
      icon: Sparkles, 
      title: 'Calculating Price', 
      description: 'Pricing agent determining optimal cost',
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    },
    { 
      icon: Zap, 
      title: 'Finding Driver', 
      description: 'Matching with best available driver',
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    { 
      icon: CheckCircle, 
      title: 'Planning Route', 
      description: 'Optimizing delivery path',
      color: 'text-orange-600',
      bgColor: 'bg-orange-100'
    }
  ]

  useEffect(() => {
    if (!isOpen) {
      setCurrentStep(0)
      setCompletedSteps([])
      return
    }

    const interval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev < steps.length - 1) {
          setCompletedSteps(completed => [...completed, prev])
          return prev + 1
        }
        return prev
      })
    }, 1500)

    return () => clearInterval(interval)
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 animate-scaleIn">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
            <Brain className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            AI Processing Order
          </h2>
          <p className="text-gray-600 text-sm">
            Our intelligent agents are working on your delivery
          </p>
        </div>

        {/* Order Info */}
        {orderData && (
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600">Route:</span>
              <span className="font-semibold text-gray-900">
                {orderData.pickup_city} → {orderData.delivery_city}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Service:</span>
              <span className="font-semibold text-gray-900 capitalize">
                {orderData.service_type}
              </span>
            </div>
          </div>
        )}

        {/* Steps */}
        <div className="space-y-4">
          {steps.map((step, index) => {
            const Icon = step.icon
            const isCompleted = completedSteps.includes(index)
            const isCurrent = currentStep === index
            const isPending = index > currentStep

            return (
              <div
                key={index}
                className={`flex items-center gap-4 p-4 rounded-lg transition-all duration-500 ${
                  isCurrent ? 'bg-blue-50 scale-105' : 
                  isCompleted ? 'bg-green-50' : 
                  'bg-gray-50 opacity-50'
                }`}
              >
                <div className={`w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 ${
                  isCompleted ? 'bg-green-500' : 
                  isCurrent ? step.bgColor : 
                  'bg-gray-200'
                }`}>
                  {isCompleted ? (
                    <CheckCircle className="w-6 h-6 text-white" />
                  ) : isCurrent ? (
                    <Icon className={`w-6 h-6 ${step.color} animate-bounce`} />
                  ) : (
                    <Icon className="w-6 h-6 text-gray-400" />
                  )}
                </div>
                <div className="flex-1">
                  <h3 className={`font-semibold ${
                    isCompleted ? 'text-green-700' : 
                    isCurrent ? 'text-gray-900' : 
                    'text-gray-500'
                  }`}>
                    {step.title}
                  </h3>
                  <p className={`text-sm ${
                    isCurrent ? 'text-gray-600' : 'text-gray-400'
                  }`}>
                    {step.description}
                  </p>
                </div>
                {isCurrent && (
                  <Loader className="w-5 h-5 text-blue-600 animate-spin" />
                )}
              </div>
            )
          })}
        </div>

        {/* Progress Bar */}
        <div className="mt-6">
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-500 ease-out"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            />
          </div>
          <p className="text-center text-sm text-gray-600 mt-2">
            {Math.round(((currentStep + 1) / steps.length) * 100)}% Complete
          </p>
        </div>

        {/* AI Badge */}
        <div className="mt-6 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-50 to-purple-50 rounded-full">
            <Sparkles className="w-4 h-4 text-purple-600" />
            <span className="text-sm font-medium text-gray-700">
              Powered by AI Agents
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
