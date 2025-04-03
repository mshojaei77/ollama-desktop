import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter
  } from '../../components/ui/dialog'
  import { Input } from '../../components/ui/input'
  import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
  } from '../../components/ui/select'
  import { Button } from '../../components/ui/button'
  import { MCPServer } from '@renderer/fetch/types'
  import { useState, useEffect } from 'react'
  import apiClient from '@renderer/fetch/api-client'
  import { toast } from 'sonner'
  
  const EditServerDialog = ({
    isDialogOpen,
    setIsDialogOpen,
    serverName,
    serverConfig,
    onServerUpdated
  }: {
    isDialogOpen: boolean
    setIsDialogOpen: (isOpen: boolean) => void
    serverName: string
    serverConfig: MCPServer
    onServerUpdated?: () => void
  }): JSX.Element => {
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [isJsonMode, setIsJsonMode] = useState(false)
    const [jsonConfig, setJsonConfig] = useState('')
    const [editedServer, setEditedServer] = useState({
      name: serverName,
      command: serverConfig.command || '',
      type: serverConfig.type || 'stdio',
      args: Array.isArray(serverConfig.args) ? serverConfig.args.join(' ') : '',
      serverUrl: serverConfig.url || ''
    })
    
    useEffect(() => {
      // Generate JSON representation for JSON mode
      const serverJson = {
        mcpServers: {
          [serverName]: {
            ...(serverConfig.type === 'sse' 
              ? { type: 'sse', url: serverConfig.url } 
              : { 
                  command: serverConfig.command,
                  args: Array.isArray(serverConfig.args) ? serverConfig.args : []
                }
            ),
            ...(serverConfig.tools && { tools: serverConfig.tools })
          }
        }
      }
      setJsonConfig(JSON.stringify(serverJson, null, 2))
    }, [serverName, serverConfig])
    
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
      const { name, value } = e.target
      setEditedServer((prev) => ({ ...prev, [name]: value }))
    }
  
    const handleTypeChange = (value: string): void => {
      setEditedServer((prev) => ({ ...prev, type: value }))
    }
    
    const handleJsonChange = (e: React.ChangeEvent<HTMLTextAreaElement>): void => {
      setJsonConfig(e.target.value)
    }
  
    const handleUpdateServer = async (): Promise<void> => {
      try {
        // Validate required fields
        if (!editedServer.name.trim()) {
          toast.error('Server name is required')
          return
        }
        
        // Validate type-specific required fields
        if (editedServer.type === 'stdio' && !editedServer.command.trim()) {
          toast.error('Command is required for STDIO servers')
          return
        }
        
        if (editedServer.type === 'sse' && !editedServer.serverUrl.trim()) {
          toast.error('Server URL is required for SSE servers')
          return
        }
        
        setIsSubmitting(true)
        
        // Parse arguments string into an array, respecting quotes
        const args = editedServer.args
          ? editedServer.args.match(/(?:[^\s"]+|"[^"]*")+/g)?.map(arg => 
              arg.startsWith('"') && arg.endsWith('"') ? arg.slice(1, -1) : arg
            ) || []
          : []
        
        // Prepare payload based on server type
        const payload = {
          server_name: editedServer.name,
          server_type: editedServer.type,
          ...(editedServer.type === 'stdio' && { 
            command: editedServer.command,
            args: args
          }),
          ...(editedServer.type === 'sse' && { 
            server_url: editedServer.serverUrl 
          }),
          tools: serverConfig.tools
        }
        
        // If server name is changed, we need to delete the old one and create a new one
        if (editedServer.name !== serverName) {
          // First create the new server
          await apiClient.post('/mcp/servers/add', payload)
          // Then delete the old one
          await apiClient.delete(`/mcp/servers/${serverName}`)
          toast.success(`Server renamed from "${serverName}" to "${editedServer.name}"`)
        } else {
          // Update existing server
          await apiClient.put(`/mcp/servers/${serverName}`, payload)
          toast.success(`Server "${serverName}" updated successfully`)
        }
        
        // Close dialog and refresh
        setIsDialogOpen(false)
        if (onServerUpdated) onServerUpdated()
      } catch (error: any) {
        console.error('Error updating server:', error)
        const errorMessage = error.response?.data?.detail || 'Failed to update server'
        toast.error(errorMessage)
      } finally {
        setIsSubmitting(false)
      }
    }
    
    const handleUpdateFromJson = async (): Promise<void> => {
      try {
        setIsSubmitting(true)
        
        // Parse JSON
        let parsedJson;
        try {
          parsedJson = JSON.parse(jsonConfig)
        } catch (error) {
          toast.error('Invalid JSON format')
          return
        }
        
        // Validate JSON structure
        if (!parsedJson.mcpServers || typeof parsedJson.mcpServers !== 'object') {
          toast.error('JSON must contain an "mcpServers" object')
          return
        }
        
        // Get the first server from the JSON (we only support editing one server at a time)
        const serverEntries = Object.entries(parsedJson.mcpServers)
        if (serverEntries.length === 0) {
          toast.error('No server configuration found in JSON')
          return
        }
        
        const [newServerName, newServerConfig] = serverEntries[0] as [string, any]
        
        // Prepare payload
        const serverType = newServerConfig.url ? 'sse' : 'stdio'
        const payload = {
          server_name: newServerName,
          server_type: serverType,
          ...(serverType === 'stdio' && { 
            command: newServerConfig.command || '',
            args: Array.isArray(newServerConfig.args) ? newServerConfig.args : []
          }),
          ...(serverType === 'sse' && { 
            server_url: newServerConfig.url || ''
          }),
          tools: newServerConfig.tools || []
        }
        
        // If server name is changed, delete old and create new
        if (newServerName !== serverName) {
          await apiClient.post('/mcp/servers/add', payload)
          await apiClient.delete(`/mcp/servers/${serverName}`)
          toast.success(`Server renamed from "${serverName}" to "${newServerName}"`)
        } else {
          await apiClient.put(`/mcp/servers/${serverName}`, payload)
          toast.success(`Server "${serverName}" updated successfully`)
        }
        
        // Close dialog and refresh
        setIsDialogOpen(false)
        if (onServerUpdated) onServerUpdated()
      } catch (error: any) {
        console.error('Error updating server from JSON:', error)
        const errorMessage = error.response?.data?.detail || 'Failed to update server'
        toast.error(errorMessage)
      } finally {
        setIsSubmitting(false)
      }
    }
  
    return (
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="bg-white text-black">
          <DialogHeader>
            <DialogTitle>Edit MCP Server: {serverName}</DialogTitle>
          </DialogHeader>
          
          <div className="mb-4">
            <div className="flex gap-2 border-b pb-2">
              <Button 
                variant={!isJsonMode ? "default" : "outline"}
                onClick={() => setIsJsonMode(false)}
                className={!isJsonMode ? "bg-blue-500 text-white hover:bg-blue-600" : "bg-white hover:bg-gray-100"}
              >
                Form
              </Button>
              <Button 
                variant={isJsonMode ? "default" : "outline"}
                onClick={() => setIsJsonMode(true)}
                className={isJsonMode ? "bg-blue-500 text-white hover:bg-blue-600" : "bg-white hover:bg-gray-100"}
              >
                JSON
              </Button>
            </div>
          </div>
          
          {!isJsonMode ? (
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <label htmlFor="name" className="text-right font-medium">
                  Name
                </label>
                <Input
                  id="name"
                  name="name"
                  value={editedServer.name}
                  onChange={handleInputChange}
                  className="col-span-3 bg-white text-black border-gray-300"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <label htmlFor="type" className="text-right font-medium">
                  Type
                </label>
                <Select value={editedServer.type} onValueChange={handleTypeChange}>
                  <SelectTrigger className="col-span-3 bg-white text-black border-gray-300">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent className="bg-white text-black">
                    <SelectItem value="stdio">stdio</SelectItem>
                    <SelectItem value="sse">sse</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              {/* Conditional fields based on type */}
              {editedServer.type === 'stdio' && (
                <>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <label htmlFor="command" className="text-right font-medium">
                      Command
                    </label>
                    <Input
                      id="command"
                      name="command"
                      value={editedServer.command}
                      onChange={handleInputChange}
                      className="col-span-3 bg-white text-black border-gray-300"
                    />
                  </div>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <label htmlFor="args" className="text-right font-medium">
                      Arguments
                    </label>
                    <Input
                      id="args"
                      name="args"
                      value={editedServer.args}
                      onChange={handleInputChange}
                      className="col-span-3 bg-white text-black border-gray-300"
                      placeholder="Space-separated arguments"
                    />
                  </div>
                </>
              )}
              
              {editedServer.type === 'sse' && (
                <div className="grid grid-cols-4 items-center gap-4">
                  <label htmlFor="serverUrl" className="text-right font-medium">
                    Server URL
                  </label>
                  <Input
                    id="serverUrl"
                    name="serverUrl"
                    value={editedServer.serverUrl}
                    onChange={handleInputChange}
                    className="col-span-3 bg-white text-black border-gray-300"
                  />
                </div>
              )}
              
              <DialogFooter className="pt-4">
                <Button
                  type="submit"
                  onClick={handleUpdateServer}
                  className="bg-white text-black border border-gray-300 hover:bg-gray-100"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Updating...' : 'Update Server'}
                </Button>
              </DialogFooter>
            </div>
          ) : (
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-1 gap-4">
                <label htmlFor="jsonConfig" className="font-medium">
                  Edit JSON Configuration
                </label>
                <textarea
                  id="jsonConfig"
                  value={jsonConfig}
                  onChange={handleJsonChange}
                  className="h-48 w-full p-2 bg-white text-black border border-gray-300 rounded font-mono"
                />
              </div>
              
              <DialogFooter className="pt-4">
                <Button
                  type="submit"
                  onClick={handleUpdateFromJson}
                  className="bg-white text-black border border-gray-300 hover:bg-gray-100"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Updating...' : 'Update From JSON'}
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    )
  }
  
  export default EditServerDialog