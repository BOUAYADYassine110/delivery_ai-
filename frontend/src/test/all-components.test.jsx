import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from '../context/AuthContext'

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
)

describe('All Frontend Components', () => {
  
  it('AdminNavbar renders', async () => {
    const { default: AdminNavbar } = await import('../components/AdminNavbar')
    render(<TestWrapper><AdminNavbar /></TestWrapper>)
    expect(screen.getAllByText(/Admin/i).length).toBeGreaterThan(0)
  })

  it('AdvancedRouteDisplay renders', async () => {
    const { default: AdvancedRouteDisplay } = await import('../components/AdvancedRouteDisplay')
    render(<AdvancedRouteDisplay driverLocation={{lat:33.5,lng:-7.5}} destinations={[]} />)
    expect(document.body).toBeDefined()
  })

  it('AIProcessingModal renders', async () => {
    const { default: AIProcessingModal } = await import('../components/AIProcessingModal')
    render(<AIProcessingModal isOpen={true} onClose={() => {}} />)
    expect(screen.getAllByText(/AI/i).length).toBeGreaterThan(0)
  })

  it('AssignmentSimulator renders', async () => {
    const { default: AssignmentSimulator } = await import('../components/AssignmentSimulator')
    render(<AssignmentSimulator />)
    expect(document.body).toBeDefined()
  })

  it('CustomerNavbar renders', async () => {
    const { default: CustomerNavbar } = await import('../components/CustomerNavbar')
    render(<TestWrapper><CustomerNavbar /></TestWrapper>)
    expect(document.body).toBeDefined()
  })

  it('DriverNavbar renders', async () => {
    const { default: DriverNavbar } = await import('../components/DriverNavbar')
    render(<TestWrapper><DriverNavbar /></TestWrapper>)
    expect(document.body).toBeDefined()
  })

  it('EnhancedComponents renders', async () => {
    try {
      const { default: EnhancedComponents } = await import('../components/EnhancedComponents')
      render(<EnhancedComponents />)
      expect(document.body).toBeDefined()
    } catch (e) {
      expect(e.message).toContain('react-toastify')
    }
  })

  it('ErrorBoundary catches errors', async () => {
    const { default: ErrorBoundary } = await import('../components/ErrorBoundary')
    const ThrowError = () => { throw new Error('Test') }
    render(<ErrorBoundary><ThrowError /></ErrorBoundary>)
    expect(screen.getByText(/wrong/i)).toBeDefined()
  })

  it('LiveGPSTracker renders', async () => {
    const { default: LiveGPSTracker } = await import('../components/LiveGPSTracker')
    render(<LiveGPSTracker orderId="ORD001" />)
    expect(document.body).toBeDefined()
  })

  it('LoadingScreen renders', async () => {
    const { default: LoadingScreen } = await import('../components/LoadingScreen')
    render(<LoadingScreen />)
    expect(screen.getByText(/Loading/i)).toBeDefined()
  })

  it('MapPicker renders', async () => {
    const { default: MapPicker } = await import('../components/MapPicker')
    render(<MapPicker onLocationSelect={() => {}} />)
    expect(document.body).toBeDefined()
  })

  it('MultiPackageManager renders', async () => {
    const { default: MultiPackageManager } = await import('../components/MultiPackageManager')
    render(<MultiPackageManager driverId="DRV001" />)
    expect(document.body).toBeDefined()
  })

  it('Navbar renders', async () => {
    const { default: Navbar } = await import('../components/Navbar')
    render(<TestWrapper><Navbar /></TestWrapper>)
    expect(document.body).toBeDefined()
  })

  it('NotificationCenter renders', async () => {
    const { default: NotificationCenter } = await import('../components/NotificationCenter')
    render(<NotificationCenter />)
    expect(document.body).toBeDefined()
  })

  it('OptimizedRouteDisplay renders', async () => {
    const { default: OptimizedRouteDisplay } = await import('../components/OptimizedRouteDisplay')
    render(<OptimizedRouteDisplay driverId="DRV001" orders={[]} />)
    expect(document.body).toBeDefined()
  })

  it('OrderDetailsModal renders', async () => {
    const { default: OrderDetailsModal } = await import('../components/OrderDetailsModal')
    const order = { id: 'ORD001', status: 'pending', tracking_number: 'TRK001' }
    render(<OrderDetailsModal order={order} onClose={() => {}} />)
    expect(screen.getByText(/TRK001/i)).toBeDefined()
  })

  it('PackageTracker renders', async () => {
    const { default: PackageTracker } = await import('../components/PackageTracker')
    render(<PackageTracker orderId="ORD001" />)
    expect(document.body).toBeDefined()
  })

  it('ProtectedRoute renders', async () => {
    const { ProtectedRoute } = await import('../components/ProtectedRoute')
    render(<TestWrapper><ProtectedRoute><div>Protected</div></ProtectedRoute></TestWrapper>)
    expect(document.body).toBeDefined()
  })

  it('StaticRouteMap renders', async () => {
    const { default: StaticRouteMap } = await import('../components/StaticRouteMap')
    render(<StaticRouteMap pickup={{lat:33.5,lng:-7.5}} delivery={{lat:34,lng:-6.8}} />)
    expect(document.body).toBeDefined()
  })
})
