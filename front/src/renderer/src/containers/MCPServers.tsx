import React, { useState } from 'react'
import { useMCPServers } from '../fetch/queries'
import { Button } from '../components/ui/button'
import NewServerDialog from './mcp/NewServerDialog'
import ServersTable from './mcp/ServersTable'

const MCPServers: React.FC = () => {
  const { data: mcpServers, isLoading, error } = useMCPServers()
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  return (
    <div className="flex flex-col p-4 h-full max-h-screen bg-[hsl(var(--background))] px-20">
      <h1 className="text-5xl font-bold mb-4">MCP Servers</h1>
      <div className="flex justify-between items-center mb-10">
        <p className=" text-gray-500">Manage your MCP server connections.</p>
        <Button onClick={() => setIsDialogOpen(true)}>Add MCP Server</Button>
      </div>

      {isLoading && <div className="text-center py-8">Loading...</div>}
      {error && <div className="text-red-500 py-4">Error: {error.message}</div>}

      {mcpServers && Object.keys(mcpServers?.servers || {}).length > 0 && (
        <div className="space-y-6">
          {Object.entries(mcpServers.servers).map(([serverName, serverConfig]) => (
            <ServersTable key={serverName} serverName={serverName} serverConfig={serverConfig} />
          ))}
        </div>
      )}

      {mcpServers && Object.keys(mcpServers?.servers || {}).length === 0 && (
        <div className="text-center py-8 bg-gray-800 rounded-lg">
          <p className="text-xl">No MCP servers configured yet.</p>
        </div>
      )}

      <NewServerDialog isDialogOpen={isDialogOpen} setIsDialogOpen={setIsDialogOpen} />
    </div>
  )
}

export default MCPServers
