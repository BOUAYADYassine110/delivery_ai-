import React from 'react'

export default function TestPage() {
  return (
    <div>
      <h1>TEST PAGE - React is working!</h1>
      <p>If you see this, React is rendering correctly.</p>
      <div style={{ 
        backgroundColor: 'lightblue', 
        padding: '20px', 
        margin: '20px',
        border: '2px solid blue'
      }}>
        <h2>Dashboard Test</h2>
        <p>Current time: {new Date().toLocaleString()}</p>
        <button onClick={() => alert('Button works!')}>
          Click me
        </button>
      </div>
    </div>
  )
}