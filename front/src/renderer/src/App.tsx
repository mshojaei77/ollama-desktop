import { useEffect } from 'react'
import Chat from './containers/Chat'
import Sidebar from './containers/Sidebar'
import MCPServers from './containers/MCPServers'
import Settings from './containers/Settings'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './fetch/queries'
import { HashRouter, Routes, Route } from 'react-router-dom'
import { Routes as AppRoutes } from './lib/routes'

function App(): JSX.Element {
  // Initialize theme from localStorage when app loads
  useEffect(() => {
    const initializeTheme = () => {
      const savedTheme = localStorage.getItem('theme') || 'system'
      const root = window.document.documentElement
      
      // Remove any existing theme class
      root.classList.remove('dark', 'light')
      
      if (savedTheme === 'system') {
        // Check system preference
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        systemPrefersDark ? root.classList.add('dark') : root.classList.add('light')
        
        // Add listener for system theme changes
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
        const handleChange = (e: MediaQueryListEvent) => {
          root.classList.remove('dark', 'light')
          e.matches ? root.classList.add('dark') : root.classList.add('light')
        }
        
        mediaQuery.addEventListener('change', handleChange)
        return () => mediaQuery.removeEventListener('change', handleChange)
      } else {
        // Apply the selected theme directly
        root.classList.add(savedTheme)
      }
    }
    
    initializeTheme()
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      <HashRouter>
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <div className="flex-1">
            <Routes>
              <Route path={AppRoutes.HOME} element={<Chat />} />
              <Route path={AppRoutes.MCP_SERVERS} element={<MCPServers />} />
              <Route path={AppRoutes.SETTINGS} element={<Settings />} />
            </Routes>
          </div>
        </div>
      </HashRouter>
    </QueryClientProvider>
  )
}

export default App
