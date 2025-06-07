import { useState, useEffect } from 'react'
import { X, Plus, Trash2, Save, AlertCircle } from 'lucide-react'

interface MCPServerConfig {
  command?: string
  url?: string
  env?: Record<string, string>
}

interface CreateMCPAgentProps {
  onClose: () => void
  onAgentCreated: () => void
}

interface CreateMCPAgentRequest {
  name: string
  description: string
  instructions: string[]
  model_name: string
  mcp_servers: MCPServerConfig[]
  tags: string[]
  example_prompts: string[]
}

const mcpAgentService = {
  async createAgent(request: CreateMCPAgentRequest) {
    const response = await fetch('/api/mcp-agents/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })
    
    if (!response.ok) {
      throw new Error('Failed to create MCP agent')
    }
    
    return await response.json()
  },

  async getAvailableModels(): Promise<string[]> {
    const response = await fetch('/api/mcp-agents/models/available')
    if (!response.ok) {
      throw new Error('Failed to fetch available models')
    }
    const data = await response.json()
    return data.models || []
  }
}

function CreateMCPAgent({ onClose, onAgentCreated }: CreateMCPAgentProps): JSX.Element {
  const [formData, setFormData] = useState<CreateMCPAgentRequest>({
    name: '',
    description: '',
    instructions: [''],
    model_name: '',
    mcp_servers: [],
    tags: [],
    example_prompts: ['']
  })
  
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [newTag, setNewTag] = useState('')

  // Load available models
  useEffect(() => {
    const loadModels = async () => {
      try {
        const models = await mcpAgentService.getAvailableModels()
        
        if (models.length === 0) {
          console.log('No models available, clearing selection.')
          setError('No models available. Please ensure Ollama is running and has models installed.')
          // Set a default model even if none are available
          setFormData(prev => ({ ...prev, model_name: 'llama3.2' }))
        } else {
          setAvailableModels(models)
          if (!formData.model_name) {
            setFormData(prev => ({ ...prev, model_name: models[0] }))
          }
        }
      } catch (err) {
        console.error('Failed to load models:', err)
        setError('Failed to load available models')
        // Set a default model on error
        setFormData(prev => ({ ...prev, model_name: 'llama3.2' }))
      }
    }
    
    loadModels()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      // Validate required fields
      if (!formData.name.trim()) {
        throw new Error('Agent name is required')
      }
      if (!formData.model_name) {
        throw new Error('Model selection is required')
      }

      // Filter out empty instructions and prompts
      const cleanedData = {
        ...formData,
        instructions: formData.instructions.filter(inst => inst.trim()),
        example_prompts: formData.example_prompts.filter(prompt => prompt.trim())
      }

      await mcpAgentService.createAgent(cleanedData)
      onAgentCreated()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create agent')
    } finally {
      setIsLoading(false)
    }
  }

  const addInstruction = () => {
    setFormData(prev => ({
      ...prev,
      instructions: [...prev.instructions, '']
    }))
  }

  const updateInstruction = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      instructions: prev.instructions.map((inst, i) => i === index ? value : inst)
    }))
  }

  const removeInstruction = (index: number) => {
    setFormData(prev => ({
      ...prev,
      instructions: prev.instructions.filter((_, i) => i !== index)
    }))
  }

  const addMCPServer = () => {
    setFormData(prev => ({
      ...prev,
      mcp_servers: [...prev.mcp_servers, { command: '', env: {} }]
    }))
  }

  const updateMCPServer = (index: number, field: keyof MCPServerConfig, value: any) => {
    setFormData(prev => ({
      ...prev,
      mcp_servers: prev.mcp_servers.map((server, i) => 
        i === index ? { ...server, [field]: value } : server
      )
    }))
  }

  const removeMCPServer = (index: number) => {
    setFormData(prev => ({
      ...prev,
      mcp_servers: prev.mcp_servers.filter((_, i) => i !== index)
    }))
  }

  const addTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }))
      setNewTag('')
    }
  }

  const removeTag = (tag: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(t => t !== tag)
    }))
  }

  const addExamplePrompt = () => {
    setFormData(prev => ({
      ...prev,
      example_prompts: [...prev.example_prompts, '']
    }))
  }

  const updateExamplePrompt = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      example_prompts: prev.example_prompts.map((prompt, i) => i === index ? value : prompt)
    }))
  }

  const removeExamplePrompt = (index: number) => {
    setFormData(prev => ({
      ...prev,
      example_prompts: prev.example_prompts.filter((_, i) => i !== index)
    }))
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-semibold text-foreground">Create MCP Agent</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-accent/20 rounded-full transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col h-full">
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {error && (
              <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3 flex items-center gap-2">
                <AlertCircle size={16} className="text-destructive" />
                <span className="text-destructive text-sm">{error}</span>
              </div>
            )}

            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-foreground">Basic Information</h3>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Agent Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Enter agent name"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Describe what this agent does"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Model *
                </label>
                <select
                  value={formData.model_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, model_name: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                >
                  {availableModels.length > 0 ? (
                    <>
                      <option value="">Select a model</option>
                      {availableModels.map(model => (
                        <option key={model} value={model}>{model}</option>
                      ))}
                    </>
                  ) : (
                    <>
                      <option value="llama3.2">llama3.2 (default)</option>
                      <option value="llama3.1">llama3.1</option>
                      <option value="qwen2.5">qwen2.5</option>
                      <option value="mistral">mistral</option>
                    </>
                  )}
                </select>
                {availableModels.length === 0 && (
                  <p className="text-orange-400 text-xs mt-1">
                    ⚠️ No models detected. Please ensure Ollama is running and has models installed.
                  </p>
                )}
              </div>
            </div>

            {/* Instructions */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-foreground">Instructions</h3>
                <button
                  type="button"
                  onClick={addInstruction}
                  className="px-3 py-1 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors flex items-center gap-1"
                >
                  <Plus size={14} />
                  Add
                </button>
              </div>
              
              {formData.instructions.map((instruction, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={instruction}
                    onChange={(e) => updateInstruction(index, e.target.value)}
                    className="flex-1 px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="Enter instruction"
                  />
                  {formData.instructions.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeInstruction(index)}
                      className="p-2 text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              ))}
            </div>

            {/* MCP Servers */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-foreground">MCP Servers</h3>
                <button
                  type="button"
                  onClick={addMCPServer}
                  className="px-3 py-1 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors flex items-center gap-1"
                >
                  <Plus size={14} />
                  Add Server
                </button>
              </div>
              
              {formData.mcp_servers.map((server, index) => (
                <div key={index} className="border border-border rounded-md p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-foreground">Server {index + 1}</h4>
                    <button
                      type="button"
                      onClick={() => removeMCPServer(index)}
                      className="p-1 text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Command
                    </label>
                    <input
                      type="text"
                      value={server.command || ''}
                      onChange={(e) => updateMCPServer(index, 'command', e.target.value)}
                      className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                      placeholder="e.g., npx -y @modelcontextprotocol/server-filesystem ."
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      URL (alternative to command)
                    </label>
                    <input
                      type="url"
                      value={server.url || ''}
                      onChange={(e) => updateMCPServer(index, 'url', e.target.value)}
                      className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                      placeholder="e.g., http://localhost:8000/mcp"
                    />
                  </div>
                </div>
              ))}
              
              {formData.mcp_servers.length === 0 && (
                <p className="text-muted-foreground text-sm">
                  No MCP servers configured. Add servers to enable external tool integration.
                </p>
              )}
            </div>

            {/* Tags */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-foreground">Tags</h3>
              
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                  className="flex-1 px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Add a tag"
                />
                <button
                  type="button"
                  onClick={addTag}
                  className="px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                >
                  Add
                </button>
              </div>
              
              {formData.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map(tag => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-accent/20 text-accent-foreground rounded-md text-sm"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => removeTag(tag)}
                        className="hover:text-destructive transition-colors"
                      >
                        <X size={12} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Example Prompts */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-foreground">Example Prompts</h3>
                <button
                  type="button"
                  onClick={addExamplePrompt}
                  className="px-3 py-1 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors flex items-center gap-1"
                >
                  <Plus size={14} />
                  Add
                </button>
              </div>
              
              {formData.example_prompts.map((prompt, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={prompt}
                    onChange={(e) => updateExamplePrompt(index, e.target.value)}
                    className="flex-1 px-3 py-2 border border-border rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="Enter example prompt"
                  />
                  {formData.example_prompts.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeExamplePrompt(index)}
                      className="p-2 text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-border p-6 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-border rounded-md hover:bg-accent/20 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              <Save size={16} />
              {isLoading ? 'Creating...' : 'Create Agent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateMCPAgent 