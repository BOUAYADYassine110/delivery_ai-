import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App-minimal'
import './index.css'

// Force clear everything
try {
  localStorage.clear()
  sessionStorage.clear()
} catch (e) {}

const root = document.getElementById('root')
if (root) {
  ReactDOM.createRoot(root).render(<App />)
} else {
  document.body.innerHTML = '<div>Error: Root element not found</div>'
}