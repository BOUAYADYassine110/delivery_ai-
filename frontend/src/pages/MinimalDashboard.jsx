import React, { useState, useEffect } from 'react'

export default function MinimalDashboard() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchOrders()
  }, [])

  const fetchOrders = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/orders')
      const data = await response.json()
      setOrders(Array.isArray(data) ? data : [])
    } catch (error) {
      console.error('Error:', error)
      setOrders([])
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
        <h1>Loading...</h1>
      </div>
    )
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '20px', color: '#333' }}>
          Dashboard
        </h1>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '30px' }}>
          <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#666' }}>Total Orders</h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: '0', color: '#333' }}>{orders.length}</p>
          </div>
          
          <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#666' }}>In Transit</h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: '0', color: '#333' }}>
              {orders.filter(o => o.status === 'in_transit').length}
            </p>
          </div>
          
          <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#666' }}>Delivered</h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: '0', color: '#333' }}>
              {orders.filter(o => o.status === 'delivered').length}
            </p>
          </div>
          
          <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#666' }}>Pending</h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', margin: '0', color: '#333' }}>
              {orders.filter(o => o.status.includes('pending')).length}
            </p>
          </div>
        </div>

        <div style={{ backgroundColor: 'white', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
          <div style={{ padding: '20px', borderBottom: '1px solid #eee' }}>
            <h2 style={{ margin: '0', fontSize: '20px', fontWeight: 'bold', color: '#333' }}>Recent Orders</h2>
          </div>
          
          {orders.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center' }}>
              <p style={{ color: '#666', fontSize: '16px' }}>No orders found</p>
              <a 
                href="/create" 
                style={{ 
                  display: 'inline-block', 
                  marginTop: '10px', 
                  padding: '10px 20px', 
                  backgroundColor: '#007bff', 
                  color: 'white', 
                  textDecoration: 'none', 
                  borderRadius: '4px' 
                }}
              >
                Create Order
              </a>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa' }}>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #eee' }}>Tracking #</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #eee' }}>From</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #eee' }}>To</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #eee' }}>Status</th>
                    <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #eee' }}>Price</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order, index) => (
                    <tr key={order.id || index} style={{ borderBottom: '1px solid #f0f0f0' }}>
                      <td style={{ padding: '12px' }}>
                        <span style={{ fontFamily: 'monospace', color: '#007bff', fontWeight: 'bold' }}>
                          {order.tracking_number || order.id}
                        </span>
                      </td>
                      <td style={{ padding: '12px' }}>{order.sender_name || 'N/A'}</td>
                      <td style={{ padding: '12px' }}>{order.receiver_name || 'N/A'}</td>
                      <td style={{ padding: '12px' }}>
                        <span style={{ 
                          padding: '4px 8px', 
                          borderRadius: '4px', 
                          fontSize: '12px', 
                          fontWeight: 'bold',
                          backgroundColor: order.status === 'delivered' ? '#d4edda' : 
                                         order.status === 'in_transit' ? '#d1ecf1' : '#fff3cd',
                          color: order.status === 'delivered' ? '#155724' : 
                                 order.status === 'in_transit' ? '#0c5460' : '#856404'
                        }}>
                          {order.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px', fontWeight: 'bold' }}>
                        {order.price || order.total_cost || 0} MAD
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}