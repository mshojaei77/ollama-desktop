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
import { NewServerForm } from '@renderer/fetch/types'
import { useState } from 'react'
import apiClient from '@renderer/fetch/api-client'
import { toast } from 'sonner'

const NewServerDialog = ({
  isDialogOpen,
  setIsDialogOpen,
  onServerAdded
}: {
  isDialogOpen: boolean
  setIsDialogOpen: (isOpen: boolean) => void
  onServerAdded?: () => void
}): JSX.Element => {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isJsonMode, setIsJsonMode] = useState(false)
  const [jsonConfig, setJsonConfig] = useState('')
  const [newServer, setNewServer] = useState<NewServerForm>({
    name: '',
    command: '',
    type: 'stdio',
    args: '',
    serverUrl: ''
  })
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target
    setNewServer((prev) => ({ ...prev, [name]: value }))
  }

  const handleTypeChange = (value: string): void => {
    setNewServer((prev) => ({ ...prev, type: value }))
  }
  
  const handleJsonChange = (e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>): void => {
    setJsonConfig(e.target.value)
  }

  const handleAddServer = async (): Promise<void> => {
    try {
      // Validate required fields
      if (!newServer.name.trim()) {
        toast.error('Server name is required')
        return
      }
      
      // Validate type-specific required fields
      if (newServer.type === 'stdio' && !newServer.command.trim()) {
        toast.error('Command is required for STDIO servers')
        return
      }
      
      if (newServer.type === 'sse' && !newServer.serverUrl.trim()) {
        toast.error('Server URL is required for SSE servers')
        return
      }
      
      setIsSubmitting(true)
      
      // Create a server configuration matching the format in ollama_desktop_config.json
      let serverConfig = {}
      
      if (newServer.type === 'stdio') {
        // Parse arguments string into an array, respecting quotes
        const args = newServer.args
          ? newServer.args.match(/(?:[^\s"]+|"[^"]*")+/g)?.map(arg => 
              arg.startsWith('"') && arg.endsWith('"') ? arg.slice(1, -1) : arg
            ) || []
          : []
        
        serverConfig = {
          mcpServers: {
            [newServer.name]: {
              command: newServer.command,
              args: args
            }
          }
        }
      } else if (newServer.type === 'sse') {
        serverConfig = {
          mcpServers: {
            [newServer.name]: {
              type: 'sse',
              url: newServer.serverUrl
            }
          }
        }
      }
      
      console.log('Server config to add:', serverConfig)
      
      try {
        // Try direct config.json update approach (alternative to API approach)
        // You may need to create a new endpoint in your Electron main process
        // that accepts this config and updates the JSON file directly
        const response = await apiClient.post('/update-config', serverConfig)
        console.log('Config update response:', response.data)
        
        // Show success message
        toast.success(`Server "${newServer.name}" added successfully`)
        
        // Reset the form fields
        setNewServer({ 
          name: '', 
          command: '', 
          type: 'stdio',
          args: '',
          serverUrl: ''
        })
        
        // Close the dialog
        setIsDialogOpen(false)
        
        // Trigger refresh in the parent component if callback is provided
        if (onServerAdded) {
          onServerAdded()
        }
      } catch (apiError: any) {
        console.error('API Error:', apiError)
        
        // If the /update-config endpoint fails, try the direct method
        try {
          // This is a fallback - try the original /mcp/servers endpoint
          const payload = {
            server_name: newServer.name,
            server_type: newServer.type,
            command: newServer.type === 'stdio' ? newServer.command : undefined,
            args: newServer.type === 'stdio' && newServer.args ? 
              newServer.args.match(/(?:[^\s"]+|"[^"]*")+/g)?.map(arg => 
                arg.startsWith('"') && arg.endsWith('"') ? arg.slice(1, -1) : arg
              ) : [],
            server_url: newServer.type === 'sse' ? newServer.serverUrl : undefined
          }
          
          console.log('Trying direct server payload:', payload)
          const directResponse = await apiClient.post('/mcp/servers/add', payload)
          console.log('Direct server addition response:', directResponse.data)
          
          // Show success message
          toast.success(`Server "${newServer.name}" added successfully`)
          
          // Reset the form fields and close dialog
          setNewServer({ name: '', command: '', type: 'stdio', args: '', serverUrl: '' })
          setIsDialogOpen(false)
          
          if (onServerAdded) onServerAdded()
        } catch (directError: any) {
          // Handle both API failures with detailed error message
          const status = directError.response?.status || apiError.response?.status
          const data = directError.response?.data || apiError.response?.data
          
          console.error('All API methods failed:', {
            status,
            data,
            message: directError.message || apiError.message
          })
          
          let errorMessage = 'Failed to add server'
          
          if (status === 400) {
            errorMessage = data?.detail || 'Invalid server configuration'
          } else if (status === 405) {
            errorMessage = 'API endpoint not available. Please check server configuration.'
          } else if (status === 409) {
            errorMessage = 'A server with this name already exists'
          } else if (status === 500) {
            errorMessage = 'Server error. Please check the application logs.'
          } else if (!status) {
            errorMessage = 'Network error. Please check your connection.'
          }
          
          toast.error(errorMessage)
        }
      }
    } catch (error: any) {
      console.error('Unexpected error adding server:', error)
      toast.error('Unexpected error occurred while adding server')
    } finally {
      setIsSubmitting(false)
    }
  }
  
  const handleAddFromJson = async (): Promise<void> => {
    try {
      setIsSubmitting(true)
      
      // Try to clean up potential JSON formatting issues
      let cleanedJsonConfig = jsonConfig.trim();
      
      // Attempt to parse the JSON input
      let parsedJson;
      try {
        parsedJson = JSON.parse(cleanedJsonConfig)
        console.log('Parsed JSON:', parsedJson)
      } catch (error) {
        console.error('JSON parse error:', error)
        toast.error('Invalid JSON format. Please check your input.')
        setIsSubmitting(false)
        return
      }
      
      // Validate the top-level structure of the JSON
      if (!parsedJson.mcpServers || typeof parsedJson.mcpServers !== 'object') {
        toast.error('JSON must contain an "mcpServers" object. Example: {"mcpServers": {"myServer": {"command": "uvx", "args": ["mcp-server"]}}}')
        setIsSubmitting(false)
        return
      }
      
      // Track success and failures during processing
      const results = {
        success: 0,
        failed: 0,
        errors: [] as string[]
      }
      
      // Define the structure expected by the backend API
      interface ServerPayload {
        server_name: string;
        server_type: string;
        command?: string;
        args?: string[];
        server_url?: string;
      }
      
      // Process each server defined in the "mcpServers" object
      for (const [serverName, serverConfig] of Object.entries(parsedJson.mcpServers)) {
        try {
          console.log(`Processing server "${serverName}"`, serverConfig)
          const config = serverConfig as Record<string, any>
          
          // Determine server type based on config properties ('url' implies 'sse')
          const serverType = config.url ? 'sse' : 'stdio'
          
          // Prepare the payload for this specific server
          const payload: ServerPayload = {
            server_name: serverName,
            server_type: serverType
          }
          
          // Add type-specific fields and perform validation
          if (serverType === 'stdio') {
            if (!config.command) {
              results.errors.push(`Server "${serverName}": command is required for STDIO servers`)
              results.failed++
              continue // Skip this server
            }
            payload.command = config.command
            // Ensure args is an array, default to empty array if missing or wrong type
            payload.args = Array.isArray(config.args) ? config.args : [] 
          } else { // sse
            if (!config.url) {
              results.errors.push(`Server "${serverName}": url is required for SSE servers`)
              results.failed++
              continue // Skip this server
            }
            payload.server_url = config.url
          }
          
          console.log(`Sending payload for server "${serverName}":`, payload)
          
          // Call the API to add this server
          const response = await apiClient.post('/mcp/servers/add', payload)
          console.log(`Server "${serverName}" creation response:`, response.data)
          results.success++
        } catch (error: any) {
          // Enhanced error handling
          console.error(`Error adding server "${serverName}":`, error)
          
          const status = error.response?.status
          const data = error.response?.data
          let errorMessage = `Error adding server "${serverName}"`
          
          if (status === 400) {
            errorMessage += `: ${data?.detail || 'Invalid configuration'}`
          } else if (status === 409) {
            errorMessage += ': Server with this name already exists'
          } else if (status === 500) {
            errorMessage += ': Server error'
          } else if (!status) {
            errorMessage += ': Network error'
          }
          
          results.errors.push(errorMessage)
          results.failed++
        }
      }
      
      // Verify servers were added by fetching the current servers list
      try {
        const serverListResponse = await apiClient.get('/mcp/servers')
        console.log('Server list after batch add:', serverListResponse.data)
      } catch (error) {
        console.error('Error fetching server list after batch add:', error)
      }
      
      // Show summary results to the user via toasts
      if (results.success > 0 && results.failed === 0) {
        toast.success(`Added ${results.success} servers successfully`)
      } else if (results.success > 0 && results.failed > 0) {
        toast.warning(`Added ${results.success} servers successfully, ${results.failed} failed`)
        console.error('Server add errors:', results.errors) // Log detailed errors
      } else if (results.success === 0 && results.failed > 0) {
        toast.error(`Failed to add ${results.failed} servers`)
        console.error('Server add errors:', results.errors) // Log detailed errors
      } else {
        toast.warning('No valid servers found in JSON to add')
      }
      
      // Reset form and close dialog if at least one server was added
      if (results.success > 0) {
        setJsonConfig('')
        setIsDialogOpen(false)
        // Trigger refresh in the parent component
        if (onServerAdded) {
          onServerAdded()
        }
      }
    } catch (error: any) {
      console.error('Error processing JSON:', error)
      toast.error('Error processing JSON configuration')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add MCP Server</DialogTitle>
        </DialogHeader>
        
        <div className="mb-4">
          <div className="flex gap-2 border-b border-[hsl(var(--border))] pb-2">
            <Button 
              variant={!isJsonMode ? "default" : "outline"}
              onClick={() => setIsJsonMode(false)}
              className={!isJsonMode ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] hover:bg-[hsl(var(--primary))] hover:brightness-110" : ""}
            >
              Form
            </Button>
            <Button 
              variant={isJsonMode ? "default" : "outline"}
              onClick={() => setIsJsonMode(true)}
              className={isJsonMode ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] hover:bg-[hsl(var(--primary))] hover:brightness-110" : ""}
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
                value={newServer.name}
                onChange={handleInputChange}
                className="col-span-3 bg-[hsl(var(--background))] border-[hsl(var(--border))]"
                placeholder="my-server"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <label htmlFor="type" className="text-right font-medium">
                Type
              </label>
              <Select value={newServer.type} onValueChange={handleTypeChange}>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="stdio">stdio</SelectItem>
                  <SelectItem value="sse">sse</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {/* Conditional fields based on type */}
            {newServer.type === 'stdio' && (
              <>
                <div className="grid grid-cols-4 items-center gap-4">
                  <label htmlFor="command" className="text-right font-medium">
                    Command
                  </label>
                  <Input
                    id="command"
                    name="command"
                    value={newServer.command}
                    onChange={handleInputChange}
                    className="col-span-3 bg-[hsl(var(--background))] border-[hsl(var(--border))]"
                    placeholder="npx, uvx, etc."
                  />
                </div>
                <div className="grid grid-cols-4 items-center gap-4">
                  <label htmlFor="args" className="text-right font-medium">
                    Arguments
                  </label>
                  <Input
                    id="args"
                    name="args"
                    value={newServer.args}
                    onChange={handleInputChange}
                    className="col-span-3 bg-[hsl(var(--background))] border-[hsl(var(--border))]"
                    placeholder="mcp-server-fetch"
                  />
                </div>
              </>
            )}
            
            {newServer.type === 'sse' && (
              <div className="grid grid-cols-4 items-center gap-4">
                <label htmlFor="serverUrl" className="text-right font-medium">
                  Server URL
                </label>
                <Input
                  id="serverUrl"
                  name="serverUrl"
                  value={newServer.serverUrl}
                  onChange={handleInputChange}
                  className="col-span-3 bg-[hsl(var(--background))] border-[hsl(var(--border))]"
                  placeholder="http://localhost:3000/sse"
                />
              </div>
            )}
            
            <DialogFooter className="pt-4">
              <Button
                type="submit"
                onClick={handleAddServer}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Adding...' : 'Add Server'}
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-1 gap-4">
              <label htmlFor="jsonConfig" className="font-medium">
                Paste JSON Configuration
              </label>
              <textarea
                id="jsonConfig"
                value={jsonConfig}
                onChange={handleJsonChange as any}
                className="h-48 w-full p-2 bg-[hsl(var(--background))] border-[hsl(var(--border))] rounded font-mono"
                placeholder={`{\n  "mcpServers": {\n    "calculator": {\n      "command": "uvx",\n      "args": ["mcp-server-calculator"]\n    }\n  }\n}`}
              />
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Paste a JSON object containing an "mcpServers" object with server configurations.
              </p>
            </div>
            
            <DialogFooter className="pt-4">
              <Button
                type="submit"
                onClick={handleAddFromJson}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Adding...' : 'Add From JSON'}
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

export default NewServerDialog
