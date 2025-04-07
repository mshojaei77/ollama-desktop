import React, { useState } from 'react'
import { useMCPServers } from '../fetch/queries'
import { Button } from '../components/ui/button'
import NewServerDialog from './mcp/NewServerDialog'
import ServersTable from './mcp/ServersTable'
import { ExternalLink } from 'lucide-react'

const MCPServers: React.FC = () => {
  const { data: mcpServers, isLoading, error, refetch } = useMCPServers()
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  const handleServerUpdated = () => {
    refetch()
  }
  
  const openServerStore = () => {
    // Open the external website in the user's browser
    window.open('https://www.pulsemcp.com/servers', '_blank')
  }

  return (
    <div className="flex flex-col p-4 h-full max-h-screen bg-[hsl(var(--background))] px-20">
      <h1 className="text-5xl font-bold mb-4">MCP Servers</h1>
      <div className="flex justify-between items-center mb-10">
        <p className="text-[hsl(var(--muted-foreground))]">Manage your MCP server connections.</p>
        <div className="flex gap-3">
          <Button 
            variant="outline" 
            onClick={openServerStore}
            className="flex items-center gap-2"
          >
            <ExternalLink className="h-4 w-4" />
            Browse Server Store
          </Button>
          <Button onClick={() => setIsDialogOpen(true)}>Add MCP Server</Button>
        </div>
      </div>

      {isLoading && <div className="text-center py-8">Loading...</div>}
      {error && <div className="text-red-500 py-4">Error: {error.message}</div>}

      {mcpServers && Object.keys(mcpServers?.servers || {}).length > 0 && (
        <div className="space-y-6">
          {Object.entries(mcpServers.servers).map(([serverName, serverConfig]) => (
            <ServersTable 
              key={serverName} 
              serverName={serverName} 
              serverConfig={serverConfig} 
              onServerUpdated={handleServerUpdated}
            />
          ))}
        </div>
      )}

      {mcpServers && Object.keys(mcpServers?.servers || {}).length === 0 && (
        <div className="text-center py-8 bg-[hsl(var(--card))] rounded-lg">
          <p className="text-xl">No MCP servers configured yet.</p>
        </div>
      )}

      <NewServerDialog 
        isDialogOpen={isDialogOpen} 
        setIsDialogOpen={setIsDialogOpen} 
        onServerAdded={handleServerUpdated} 
      />
    </div>
  )
}

export default MCPServers
