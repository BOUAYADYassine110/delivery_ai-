import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'
import { ProtectedRoute, PublicRoute } from '../components/ProtectedRoute'

const TestComponent = () => <div>Protected Content</div>
const PublicComponent = () => <div>Public Content</div>

const renderWithRouter = (component, initialPath = '/protected') => {
  window.history.pushState({}, '', initialPath)
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<PublicComponent />} />
          <Route path="/protected" element={component} />
          <Route path="/customer" element={<div>Customer Dashboard</div>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('should redirect to home when not authenticated', () => {
    renderWithRouter(
      <ProtectedRoute>
        <TestComponent />
      </ProtectedRoute>
    )
    
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('should render content when authenticated with correct role', () => {
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('user_role', 'customer')
    localStorage.setItem('user_data', JSON.stringify({ id: '1', name: 'Test' }))

    renderWithRouter(
      <ProtectedRoute allowedRoles={['customer']}>
        <TestComponent />
      </ProtectedRoute>,
      '/protected'
    )
    
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('should redirect when authenticated with wrong role', () => {
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('user_role', 'customer')
    localStorage.setItem('user_data', JSON.stringify({ id: '1', name: 'Test' }))

    renderWithRouter(
      <ProtectedRoute allowedRoles={['admin']}>
        <TestComponent />
      </ProtectedRoute>
    )
    
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })
})

describe('PublicRoute', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('should render content when not authenticated', () => {
    renderWithRouter(
      <PublicRoute>
        <TestComponent />
      </PublicRoute>,
      '/protected'
    )
    
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('should redirect to dashboard when authenticated', () => {
    localStorage.setItem('token', 'test-token')
    localStorage.setItem('user_role', 'customer')
    localStorage.setItem('user_data', JSON.stringify({ id: '1', name: 'Test' }))

    renderWithRouter(
      <PublicRoute>
        <TestComponent />
      </PublicRoute>
    )
    
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })
})
