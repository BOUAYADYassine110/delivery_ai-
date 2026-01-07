import { useEffect, useRef, useState } from 'react'

export function useWebSocket(url, options = {}) {
  const [data, setData] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)

  const { 
    reconnect = true, 
    reconnectInterval = 3000,
    onMessage,
    onConnect,
    onDisconnect,
    onError
  } = options

  useEffect(() => {
    if (!url) return

    const connect = () => {
      try {
        const ws = new WebSocket(url)
        wsRef.current = ws

        ws.onopen = () => {
          setIsConnected(true)
          setError(null)
          onConnect?.()
        }

        ws.onmessage = (event) => {
          try {
            const parsedData = JSON.parse(event.data)
            setData(parsedData)
            onMessage?.(parsedData)
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err)
          }
        }

        ws.onerror = (event) => {
          const errorMsg = 'WebSocket error occurred'
          setError(errorMsg)
          onError?.(errorMsg)
        }

        ws.onclose = () => {
          setIsConnected(false)
          onDisconnect?.()

          if (reconnect) {
            reconnectTimeoutRef.current = setTimeout(() => {
              connect()
            }, reconnectInterval)
          }
        }
      } catch (err) {
        setError(err.message)
        onError?.(err.message)
      }
    }

    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [url, reconnect, reconnectInterval])

  const sendMessage = (message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }

  return { data, isConnected, error, sendMessage }
}

// Hook for tracking order updates
export function useOrderTracking(orderId) {
  const url = orderId ? `ws://localhost:8001/ws/tracking/${orderId}` : null
  
  return useWebSocket(url, {
    reconnect: true,
    reconnectInterval: 5000
  })
}

// Hook for driver updates
export function useDriverUpdates(driverId) {
  const url = driverId ? `ws://localhost:8001/ws/driver/${driverId}` : null
  
  return useWebSocket(url, {
    reconnect: true,
    reconnectInterval: 5000
  })
}
