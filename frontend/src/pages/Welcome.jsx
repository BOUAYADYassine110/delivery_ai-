import { Link } from 'react-router-dom'
import { Package, Truck, MapPin, Clock, Shield, Star, ArrowRight, CheckCircle, Users, Settings, Menu, X, Zap } from 'lucide-react'
import { useState } from 'react'

export default function Welcome() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-md shadow-sm z-50 transition-all duration-300">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center gap-2 group cursor-pointer">
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <Package className="w-7 h-7 text-white" />
              </div>
              <span className="text-2xl font-bold text-gray-900">DeliveryAI</span>
            </div>

            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-700 hover:text-blue-600 font-medium transition-colors duration-200">Features</a>
              <a href="#coverage" className="text-gray-700 hover:text-blue-600 font-medium transition-colors duration-200">Coverage</a>
              <a href="#how-it-works" className="text-gray-700 hover:text-blue-600 font-medium transition-colors duration-200">How It Works</a>
              <Link to="/login" className="text-gray-700 hover:text-blue-600 font-medium transition-colors duration-200">Sign In</Link>
              <Link to="/register" className="px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 hover:shadow-lg transition-all duration-300">
                Get Started
              </Link>
            </div>

            <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="md:hidden">
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {mobileMenuOpen && (
            <div className="md:hidden py-4 space-y-3 animate-slideDown">
              <a href="#features" className="block py-2 text-gray-700 hover:text-blue-600">Features</a>
              <a href="#coverage" className="block py-2 text-gray-700 hover:text-blue-600">Coverage</a>
              <a href="#how-it-works" className="block py-2 text-gray-700 hover:text-blue-600">How It Works</a>
              <Link to="/login" className="block py-2 text-gray-700 hover:text-blue-600">Sign In</Link>
              <Link to="/register" className="block py-2 px-4 bg-blue-600 text-white rounded-lg text-center">Get Started</Link>
            </div>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 bg-gradient-to-br from-blue-50 via-white to-purple-50 overflow-hidden">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="animate-fadeInLeft">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold mb-6">
                <Zap className="w-4 h-4" />
                AI-Powered Delivery Platform
              </div>
              <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
                Fast & Reliable
                <span className="block text-blue-600">Delivery Service</span>
              </h1>
              <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                Connect with <span className="font-bold text-blue-600">16 professional drivers</span> across <span className="font-bold text-purple-600">6 cities</span> in Morocco. Real-time tracking and guaranteed delivery.
              </p>
              <div className="flex flex-wrap gap-4 mb-8">
                <Link to="/register" className="group px-8 py-4 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-all duration-300 flex items-center gap-2 shadow-lg hover:shadow-xl hover:scale-105">
                  Start Shipping Now
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link to="/system/coverage" className="px-8 py-4 bg-white text-gray-700 rounded-lg font-semibold border-2 border-gray-300 hover:border-blue-600 hover:text-blue-600 transition-all duration-300">
                  View Coverage
                </Link>
              </div>
              <div className="flex items-center gap-6 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="font-medium">99% On-Time</span>
                </div>
                <div className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-blue-600" />
                  <span className="font-medium">Insured</span>
                </div>
                <div className="flex items-center gap-2">
                  <Star className="w-5 h-5 text-yellow-500" />
                  <span className="font-medium">4.9/5</span>
                </div>
              </div>
            </div>

            {/* Delivery Illustration */}
            <div className="relative animate-fadeInRight">
              <div className="relative bg-gradient-to-br from-blue-100 to-purple-100 rounded-3xl p-12 shadow-2xl">
                {/* Delivery Van */}
                <div className="text-center mb-8 animate-float">
                  <div className="text-9xl">🚚</div>
                </div>
                
                {/* Grouped Packages */}
                <div className="relative">
                  {/* Stack of packages */}
                  <div className="flex justify-center items-end gap-2 mb-4">
                    <div className="text-7xl animate-bounce" style={{animationDelay: '0s'}}>📦</div>
                    <div className="text-7xl animate-bounce" style={{animationDelay: '0.1s'}}>📦</div>
                    <div className="text-7xl animate-bounce" style={{animationDelay: '0.2s'}}>📦</div>
                  </div>
                  <div className="flex justify-center gap-2">
                    <div className="text-6xl animate-bounce" style={{animationDelay: '0.3s'}}>📦</div>
                    <div className="text-6xl animate-bounce" style={{animationDelay: '0.4s'}}>📦</div>
                  </div>
                </div>

                {/* Floating Stats */}
                <div className="absolute -top-4 -right-4 bg-white rounded-xl shadow-xl p-4 animate-slideInRight">
                  <div className="text-3xl font-bold text-blue-600">16</div>
                  <div className="text-xs text-gray-600 font-medium">Active Drivers</div>
                </div>
                <div className="absolute -bottom-4 -left-4 bg-white rounded-xl shadow-xl p-4 animate-slideInLeft">
                  <div className="text-3xl font-bold text-green-600">6</div>
                  <div className="text-xs text-gray-600 font-medium">Cities</div>
                </div>
                <div className="absolute top-1/2 -right-6 bg-white rounded-xl shadow-xl p-3 animate-pulse">
                  <MapPin className="w-6 h-6 text-purple-600" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16 animate-fadeIn">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Why Choose DeliveryAI</h2>
            <p className="text-xl text-gray-600">Advanced features for seamless delivery</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: MapPin, title: 'Real-Time Tracking', desc: 'Track your package live with GPS accuracy', color: 'blue', delay: '0s' },
              { icon: Clock, title: 'Same-Day Delivery', desc: 'Express delivery within the same city', color: 'green', delay: '0.1s' },
              { icon: Shield, title: 'Secure & Insured', desc: 'All packages handled with maximum care', color: 'purple', delay: '0.2s' }
            ].map((feature, i) => (
              <div key={i} className={`group text-center p-8 bg-${feature.color}-50 rounded-2xl hover:shadow-xl transition-all duration-300 hover:-translate-y-2 animate-fadeInUp`} style={{animationDelay: feature.delay}}>
                <div className={`w-16 h-16 bg-${feature.color}-600 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300`}>
                  <feature.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16 animate-fadeIn">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">How It Works</h2>
            <p className="text-xl text-gray-600">Simple steps to send your package</p>
          </div>

          <div className="grid md:grid-cols-4 gap-8 max-w-5xl mx-auto">
            {[
              { num: 1, title: 'Create Order', desc: 'Enter details online', color: 'blue' },
              { num: 2, title: 'Driver Assigned', desc: 'AI assigns best driver', color: 'green' },
              { num: 3, title: 'Track Live', desc: 'Monitor in real-time', color: 'purple' },
              { num: 4, title: 'Delivered', desc: 'Arrives safely on time', color: 'orange' }
            ].map((step, i) => (
              <div key={i} className="text-center animate-fadeInUp" style={{animationDelay: `${i * 0.1}s`}}>
                <div className={`w-20 h-20 bg-${step.color}-600 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl font-bold text-white shadow-lg hover:scale-110 transition-transform duration-300`}>
                  {step.num}
                </div>
                <h4 className="font-bold text-lg mb-2">{step.title}</h4>
                <p className="text-gray-600 text-sm">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* City Coverage */}
      <section id="coverage" className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16 animate-fadeIn">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">City Coverage</h2>
            <p className="text-xl text-gray-600">Serving 6 major cities across Morocco</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            {[
              { city: 'Casablanca', drivers: 4, icon: '🏙️' },
              { city: 'Rabat', drivers: 3, icon: '🏛️' },
              { city: 'Marrakech', drivers: 3, icon: '🕌' },
              { city: 'Agadir', drivers: 2, icon: '🏖️' },
              { city: 'El Jadida', drivers: 2, icon: '🏰' },
              { city: 'Salé', drivers: 2, icon: '🌆' }
            ].map((city, i) => (
              <div key={i} className="bg-gray-50 rounded-xl p-6 text-center hover:shadow-xl transition-all duration-300 hover:-translate-y-2 animate-fadeInUp" style={{animationDelay: `${i * 0.1}s`}}>
                <div className="text-5xl mb-3">{city.icon}</div>
                <h4 className="font-bold text-lg text-gray-900 mb-1">{city.city}</h4>
                <p className="text-blue-600 font-semibold flex items-center justify-center gap-1">
                  <Truck className="w-4 h-4" />
                  {city.drivers} Drivers
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* User Portals */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16 animate-fadeIn">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Access Your Portal</h2>
            <p className="text-xl text-gray-600">Choose your role to get started</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              { icon: Users, title: 'Customer', desc: 'Send packages and track deliveries', color: 'blue', link: '/login', register: true },
              { icon: Truck, title: 'Driver', desc: 'Accept orders and earn money', color: 'green', link: '/driver/login', register: false },
              { icon: Settings, title: 'Admin', desc: 'Manage system operations', color: 'purple', link: '/admin/login', register: false }
            ].map((portal, i) => (
              <div key={i} className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 animate-fadeInUp" style={{animationDelay: `${i * 0.1}s`}}>
                <div className={`w-16 h-16 bg-${portal.color}-600 rounded-xl flex items-center justify-center mb-6 hover:scale-110 transition-transform duration-300`}>
                  <portal.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">{portal.title}</h3>
                <p className="text-gray-600 mb-6">{portal.desc}</p>
                <div className="space-y-3">
                  <Link to={portal.link} className={`block w-full text-center px-6 py-3 bg-${portal.color}-600 text-white rounded-lg font-medium hover:bg-${portal.color}-700 transition-colors`}>
                    Login
                  </Link>
                  {portal.register && (
                    <Link to="/register" className={`block w-full text-center px-6 py-3 border-2 border-${portal.color}-600 text-${portal.color}-600 rounded-lg font-medium hover:bg-${portal.color}-50 transition-colors`}>
                      Register
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-purple-600">
        <div className="container mx-auto px-4 text-center animate-fadeIn">
          <h2 className="text-4xl font-bold text-white mb-6">Ready to Ship?</h2>
          <p className="text-xl text-blue-100 mb-8">Join hundreds using our smart delivery platform</p>
          <Link to="/register" className="inline-flex items-center gap-2 px-8 py-4 bg-white text-blue-600 rounded-lg font-bold hover:shadow-2xl hover:scale-105 transition-all duration-300">
            Get Started Free
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="container mx-auto px-4 text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Package className="w-8 h-8 text-blue-500" />
            <span className="text-2xl font-bold text-white">DeliveryAI</span>
          </div>
          <p className="mb-4">Smart delivery solutions powered by AI</p>
          <p className="text-sm">© 2024 DeliveryAI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
