import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'

// Clear cache on errors
function clearCache() {
  if ('caches' in window) {
    caches.keys().then(names => {
      names.forEach(name => caches.delete(name))
    })
  }
  localStorage.removeItem('react-query-cache')
}

// Add global error handler
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error)
  clearCache()
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason)
  clearCache()
})

// Force reload on blank page
if (document.body.innerHTML.trim() === '') {
  clearCache()
  window.location.reload()
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
)
