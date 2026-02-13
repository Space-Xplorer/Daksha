import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App_integrated.jsx'
import { AuthProvider } from './context/AuthContext'
import { ApplicationProvider } from './context/ApplicationContext'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <ApplicationProvider>
        <App />
      </ApplicationProvider>
    </AuthProvider>
  </StrictMode>,
)
