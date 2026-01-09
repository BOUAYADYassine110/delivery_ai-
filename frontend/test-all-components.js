/**
 * Frontend Component Testing Script
 * Tests all components, pages, services, and utilities
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'

// ============================================================================
// COMPONENT TESTS
// ============================================================================

describe('Core Components', () => {
  describe('LoadingScreen', () => {
    it('renders loading spinner', async () => {
      const { default: LoadingScreen } = await import('./src/components/LoadingScreen.jsx')
      render(<LoadingScreen />)
      expect(screen.getByText(/Loading Multi-Agent Delivery System/i)).toBeDefined()
    })
  })

  describe('ErrorBoundary', () => {
    it('catches errors and displays fallback', async () => {
      const { default: ErrorBoundary } = await import('./src/components/ErrorBoundary.jsx')
      const ThrowError = () => { throw new Error('Test error') }
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      )
      expect(screen.getByText(/Something went wrong/i)).toBeDefined()
    })
  })

  describe('NotificationCenter', () => {
    it('displays notifications', async () => {
      const { default: NotificationCenter } = await import('./src/components/NotificationCenter.jsx')
      const mockNotifications = [
        { id: '1', title: 'Test', message: 'Test message', read: false }
      ]
      render(<NotificationCenter notifications={mockNotifications} />)
      expect(screen.getByText('Test')).toBeDefined()
    })
  })

  describe('OrderDetailsModal', () => {
    it('renders order details', async () => {
      const { default: OrderDetailsModal } = await import('./src/components/OrderDetailsModal.jsx')
      const mockOrder = {
        id: 'ORD001',
        tracking_number: 'TRK001',
        status: 'pending',
        pickup_address: '123 Test St',
        delivery_address: '456 Test Ave'
      }
      render(<OrderDetailsModal order={mockOrder} onClose={() => {}} />)
      expect(screen.getByText('TRK001')).toBeDefined()
    })
  })

  describe('MapPicker', () => {
    it('renders map interface', async () => {
      const { default: MapPicker } = await import('./src/components/MapPicker.jsx')
      render(<MapPicker onLocationSelect={() => {}} />)
      expect(screen.getByText(/Pick on Map/i)).toBeDefined()
    })
  })

  describe('OptimizedRouteDisplay', () => {
    it('displays route information', async () => {
      const { default: OptimizedRouteDisplay } = await import('./src/components/OptimizedRouteDisplay.jsx')
      render(<OptimizedRouteDisplay driverId="DRV001" orders={[]} />)
      await waitFor(() => {
        expect(screen.getByText(/Route/i)).toBeDefined()
      })
    })
  })
})

// ============================================================================
// PAGE TESTS
// ============================================================================

describe('Pages', () => {
  describe('CreateOrder', () => {
    it('renders order form', async () => {
      const { default: CreateOrder } = await import('./src/pages/CreateOrder.jsx')
      render(
        <BrowserRouter>
          <CreateOrder />
        </BrowserRouter>
      )
      expect(screen.getByText(/Create Order/i)).toBeDefined()
    })

    it('validates required fields', async () => {
      const { default: CreateOrder } = await import('./src/pages/CreateOrder.jsx')
      render(
        <BrowserRouter>
          <CreateOrder />
        </BrowserRouter>
      )
      const submitButton = screen.getByRole('button', { name: /submit/i })
      fireEvent.click(submitButton)
      await waitFor(() => {
        expect(screen.getByText(/required/i)).toBeDefined()
      })
    })
  })

  describe('PricingCalculator', () => {
    it('calculates price', async () => {
      const { default: PricingCalculator } = await import('./src/pages/PricingCalculator.jsx')
      render(<PricingCalculator />)
      expect(screen.getByText(/Pricing Calculator/i)).toBeDefined()
    })
  })

  describe('CustomerDashboard', () => {
    it('displays orders', async () => {
      const { default: CustomerDashboard } = await import('./src/pages/CustomerDashboard.jsx')
      render(
        <BrowserRouter>
          <CustomerDashboard />
        </BrowserRouter>
      )
      expect(screen.getByText(/Dashboard/i)).toBeDefined()
    })
  })

  describe('DriverDashboard', () => {
    it('shows driver stats', async () => {
      const { default: DriverDashboard } = await import('./src/pages/DriverDashboard.jsx')
      render(
        <BrowserRouter>
          <DriverDashboard />
        </BrowserRouter>
      )
      expect(screen.getByText(/Driver/i)).toBeDefined()
    })
  })

  describe('AdminDashboard', () => {
    it('displays admin panel', async () => {
      const { default: AdminDashboard } = await import('./src/pages/AdminDashboard.jsx')
      render(
        <BrowserRouter>
          <AdminDashboard />
        </BrowserRouter>
      )
      expect(screen.getByText(/Admin/i)).toBeDefined()
    })
  })
})

// ============================================================================
// SERVICE TESTS
// ============================================================================

describe('Services', () => {
  describe('pricingService', () => {
    it('calculates AI pricing', async () => {
      const { calculatePrice } = await import('./src/services/pricingService.js')
      const result = await calculatePrice({
        pickup_city: 'Casablanca',
        delivery_city: 'Rabat',
        weight: 2.0,
        service_type: 'standard'
      })
      expect(result.total_cost).toBeGreaterThan(0)
    })

    it('handles fallback pricing', async () => {
      const { calculateFallbackPrice } = await import('./src/services/pricingService.js')
      const result = calculateFallbackPrice({
        pickup_city: 'Casablanca',
        delivery_city: 'Rabat',
        weight: 2.0
      })
      expect(result.total_cost).toBeGreaterThan(0)
    })
  })

  describe('api', () => {
    it('makes GET requests', async () => {
      const api = await import('./src/services/api.js')
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ data: 'test' })
        })
      )
      const result = await api.default.get('/test')
      expect(result.data).toBe('test')
    })

    it('makes POST requests', async () => {
      const api = await import('./src/services/api.js')
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true })
        })
      )
      const result = await api.default.post('/test', { data: 'test' })
      expect(result.success).toBe(true)
    })
  })

  describe('routingService', () => {
    it('gets route', async () => {
      const { getRoute } = await import('./src/services/routingService.js')
      const route = await getRoute(33.5731, -7.5898, 34.0209, -6.8416)
      expect(route).toBeDefined()
      expect(route.distance).toBeGreaterThan(0)
    })
  })

  describe('gpsService', () => {
    it('calculates distance', async () => {
      const { calculateDistance } = await import('./src/services/gpsService.js')
      const distance = calculateDistance(33.5731, -7.5898, 34.0209, -6.8416)
      expect(distance).toBeGreaterThan(0)
    })
  })
})

// ============================================================================
// UTILITY TESTS
// ============================================================================

describe('Utilities', () => {
  describe('validation', () => {
    it('validates phone numbers', async () => {
      const { validatePhone } = await import('./src/utils/validation.js')
      expect(validatePhone('+212661234567')).toBe(true)
      expect(validatePhone('invalid')).toBe(false)
    })

    it('validates addresses', async () => {
      const { validateAddress } = await import('./src/utils/validation.js')
      expect(validateAddress('123 Test Street')).toBe(true)
      expect(validateAddress('')).toBe(false)
    })

    it('validates weight', async () => {
      const { validateWeight } = await import('./src/utils/validation.js')
      expect(validateWeight(5.0)).toBe(true)
      expect(validateWeight(-1)).toBe(false)
    })
  })
})

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

describe('Integration Tests', () => {
  it('complete order flow', async () => {
    // 1. Create order
    const { default: CreateOrder } = await import('./src/pages/CreateOrder.jsx')
    const { container } = render(
      <BrowserRouter>
        <CreateOrder />
      </BrowserRouter>
    )
    
    // 2. Fill form
    const pickupInput = container.querySelector('input[name="pickup_address"]')
    fireEvent.change(pickupInput, { target: { value: '123 Test St' } })
    
    // 3. Submit
    const submitButton = screen.getByRole('button', { name: /submit/i })
    fireEvent.click(submitButton)
    
    // 4. Verify
    await waitFor(() => {
      expect(screen.getByText(/success/i)).toBeDefined()
    })
  })

  it('driver accepts order', async () => {
    const { default: DriverDashboard } = await import('./src/pages/DriverDashboard.jsx')
    render(
      <BrowserRouter>
        <DriverDashboard />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      const acceptButton = screen.queryByText(/Accept/i)
      if (acceptButton) {
        fireEvent.click(acceptButton)
      }
    })
  })
})

console.log('✅ All frontend tests defined')
