import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider, useAuth } from '../context/AuthContext'

const wrapper = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>{children}</AuthProvider>
  </BrowserRouter>
)

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('should initialize with no user', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.user).toBeNull()
  })

  it('should login user correctly', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    
    act(() => {
      result.current.login(
        { id: '1', name: 'Test User' },
        'test-token',
        'customer'
      )
    })

    expect(result.current.user).toEqual({
      id: '1',
      name: 'Test User',
      role: 'customer',
      token: 'test-token'
    })
    expect(localStorage.getItem('token')).toBe('test-token')
    expect(localStorage.getItem('user_role')).toBe('customer')
  })

  it('should logout user correctly', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    
    act(() => {
      result.current.login({ id: '1' }, 'test-token', 'customer')
    })

    act(() => {
      result.current.logout()
    })

    expect(result.current.user).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
  })

  it('should return correct dashboard route for each role', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    
    expect(result.current.getDashboardRoute('customer')).toBe('/dashboard')
    expect(result.current.getDashboardRoute('driver')).toBe('/driver/dashboard')
    expect(result.current.getDashboardRoute('admin')).toBe('/admin/dashboard')
  })
})
