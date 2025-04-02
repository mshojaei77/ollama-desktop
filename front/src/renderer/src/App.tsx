import Chat from './containers/Chat'
import Sidebar from './containers/Sidebar'
import MCPServers from './containers/MCPServers'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './fetch/queries'
import { HashRouter, Routes, Route } from 'react-router-dom'
import { Routes as AppRoutes } from './lib/routes'

function App(): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <HashRouter>
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <div className="flex-1">
            <Routes>
              <Route path={AppRoutes.HOME} element={<Chat />} />
              <Route path={AppRoutes.MCP_SERVERS} element={<MCPServers />} />
            </Routes>
          </div>
        </div>
      </HashRouter>
    </QueryClientProvider>
  )
}

export default App
