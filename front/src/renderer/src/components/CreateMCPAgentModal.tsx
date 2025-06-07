import { useState, useEffect } from 'react'
import { X, Plus, Trash2, AlertTriangle, CheckCircle, Copy, ExternalLink, Sparkles } from 'lucide-react'
import mcpAgentService, { 
  CreateMCPAgentRequest, 
  MCPServerConfig, 
  MCPServerTemplate 
} from '../services/mcpAgentService'

interface CreateMCPAgentModalProps {
  onClose: () => void
  onSuccess: () => void
}

interface FormData {
  name: string
  description: string
  instructions: string[]
  model_name: string
  category: string
  tags: string[]
  icon: string
  example_prompts: string[]
  welcome_message: string
  mcp_servers: MCPServerConfig[]
  markdown: boolean
  show_tool_calls: boolean
  add_datetime_to_instructions: boolean
}

function CreateMCPAgentModal({ onClose, onSuccess }: CreateMCPAgentModalProps): JSX.Element {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    description: '',
    instructions: ['You are a helpful AI assistant.'],
    model_name: 'llama3.2',
    category: '',
    tags: [],
    icon: '🤖',
    example_prompts: [],
    welcome_message: '',
    mcp_servers: [],
    markdown: true,
    show_tool_calls: true,
    add_datetime_to_instructions: false
  })

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentTab, setCurrentTab] = useState<'basic' | 'mcp' | 'advanced'>('basic')
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [serverTemplates, setServerTemplates] = useState<MCPServerTemplate[]>([])
  const [showTemplates, setShowTemplates] = useState(false)
  const [newTag, setNewTag] = useState('')
  const [newPrompt, setNewPrompt] = useState('')
  const [newInstruction, setNewInstruction] = useState('')

  // Available categories
  const availableCategories = [
    'development',
    'research',
    'productivity',
    'analysis',
    'communication',
    'content',
    'travel',
    'finance'
  ]

  // Available icons
  const availableIcons = [
    '🤖', '📁', '🐙', '🔍', '✈️', '🧠', '🌿', '📊', '💼', '🎯',
    '⚡', '🔧', '📝', '🎨', '🌟', '🚀', '💡', '🔬', '📚', '🎵'
  ]

  useEffect(() => {
    fetchInitialData()
  }, [])

  const fetchInitialData = async () => {
    try {
      const [models, templates] = await Promise.all([
        mcpAgentService.getAvailableModels(),
        mcpAgentService.getMCPServerTemplates()
      ])
      setAvailableModels(models)
      setServerTemplates(templates)
    } catch (error) {
      console.error('Error fetching initial data:', error)
    }
  }

  const handleInputChange = (field: keyof FormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const addTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      handleInputChange('tags', [...formData.tags, newTag.trim()])
      setNewTag('')
    }
  }

  const removeTag = (tagToRemove: string) => {
    handleInputChange('tags', formData.tags.filter(tag => tag !== tagToRemove))
  }

  const addPrompt = () => {
    if (newPrompt.trim() && !formData.example_prompts.includes(newPrompt.trim())) {
      handleInputChange('example_prompts', [...formData.example_prompts, newPrompt.trim()])
      setNewPrompt('')
    }
  }

  const removePrompt = (promptToRemove: string) => {
    handleInputChange('example_prompts', formData.example_prompts.filter(prompt => prompt !== promptToRemove))
  }

  const addInstruction = () => {
    if (newInstruction.trim()) {
      handleInputChange('instructions', [...formData.instructions, newInstruction.trim()])
      setNewInstruction('')
    }
  }

  const removeInstruction = (index: number) => {
    handleInputChange('instructions', formData.instructions.filter((_, i) => i !== index))
  }

  const addMCPServer = () => {
    const newServer: MCPServerConfig = {
      name: `server_${formData.mcp_servers.length + 1}`,
      transport: 'stdio',
      command: '',
      enabled: true,
      description: ''
    }
    handleInputChange('mcp_servers', [...formData.mcp_servers, newServer])
  }

  const updateMCPServer = (index: number, updates: Partial<MCPServerConfig>) => {
    const updatedServers = formData.mcp_servers.map((server, i) => 
      i === index ? { ...server, ...updates } : server
    )
    handleInputChange('mcp_servers', updatedServers)
  }

  const removeMCPServer = (index: number) => {
    handleInputChange('mcp_servers', formData.mcp_servers.filter((_, i) => i !== index))
  }

  const addServerFromTemplate = (template: MCPServerTemplate) => {
    const agentRequest = mcpAgentService.createAgentFromTemplate(template)
    
    // Update form with template data
    setFormData(prev => ({
      ...prev,
      name: prev.name || agentRequest.name!,
      description: prev.description || agentRequest.description!,
      instructions: agentRequest.instructions!,
      category: agentRequest.category!,
      tags: [...new Set([...prev.tags, ...agentRequest.tags!])],
      icon: agentRequest.icon!,
      welcome_message: agentRequest.welcome_message!,
      mcp_servers: [...prev.mcp_servers, ...agentRequest.mcp_servers!]
    }))
    
    setShowTemplates(false)
    setCurrentTab('mcp')
  }

  const validateForm = (): string | null => {
    if (!formData.name.trim()) return 'Agent name is required'
    if (formData.instructions.length === 0) return 'At least one instruction is required'
    
    // Validate MCP servers
    for (let i = 0; i < formData.mcp_servers.length; i++) {
      const server = formData.mcp_servers[i]
      if (server.transport === 'stdio' && !server.command?.trim()) {
        return `MCP Server ${i + 1}: Command is required for stdio transport`
      }
      if ((server.transport === 'sse' || server.transport === 'streamable-http') && !server.url?.trim()) {
        return `MCP Server ${i + 1}: URL is required for ${server.transport} transport`
      }
    }
    
    return null
  }

  const handleSubmit = async () => {
    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const request: CreateMCPAgentRequest = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        instructions: formData.instructions.filter(inst => inst.trim()),
        model_name: formData.model_name,
        model_provider: 'ollama',
        mcp_servers: formData.mcp_servers,
        tags: formData.tags,
        category: formData.category || undefined,
        icon: formData.icon,
        example_prompts: formData.example_prompts,
        welcome_message: formData.welcome_message.trim() || undefined,
        markdown: formData.markdown,
        show_tool_calls: formData.show_tool_calls,
        add_datetime_to_instructions: formData.add_datetime_to_instructions
      }

      await mcpAgentService.createAgent(request)
      onSuccess()
    } catch (error: any) {
      console.error('Error creating agent:', error)
      setError(error.response?.data?.detail || 'Failed to create agent. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card border border-border rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <Sparkles className="w-6 h-6 text-primary" />
            <h2 className="text-xl font-semibold text-foreground">Create MCP Agent</h2>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
            disabled={isLoading}
          >
            <X size={24} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-border">
          {[
            { id: 'basic', label: 'Basic Info', desc: 'Name, description, model' },
            { id: 'mcp', label: 'MCP Servers', desc: 'External integrations' },
            { id: 'advanced', label: 'Advanced', desc: 'Behavior, prompts' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id as any)}
              className={`flex-1 px-4 py-3 text-left border-b-2 transition-colors ${
                currentTab === tab.id
                  ? 'border-primary text-primary bg-primary/5'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-accent/20'
              }`}
            >
              <div className="font-medium">{tab.label}</div>
              <div className="text-xs opacity-75">{tab.desc}</div>
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-md text-red-400 text-sm flex items-center gap-2">
              <AlertTriangle size={16} />
              {error}
            </div>
          )}

          {currentTab === 'basic' && (
            <div className="space-y-6">
              {/* Template Selection */}
              <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-medium text-primary">Quick Start Templates</h3>
                    <p className="text-xs text-muted-foreground">Choose a pre-configured template to get started quickly</p>
                  </div>
                  <button
                    onClick={() => setShowTemplates(!showTemplates)}
                    className="text-primary hover:text-primary/80 text-sm"
                  >
                    {showTemplates ? 'Hide' : 'Browse'} Templates
                  </button>
                </div>
                
                {showTemplates && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                    {serverTemplates.map(template => (
                      <div
                        key={template.name}
                        className="p-3 bg-background border border-border rounded-lg hover:border-primary/50 transition-colors cursor-pointer"
                        onClick={() => addServerFromTemplate(template)}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-lg">{template.icon}</span>
                          <span className="font-medium text-sm">{template.name}</span>
                        </div>
                        <p className="text-xs text-muted-foreground mb-2">{template.description}</p>
                        <div className="flex flex-wrap gap-1">
                          {template.tags.slice(0, 3).map(tag => (
                            <span key={tag} className="text-xs bg-accent/30 text-muted-foreground px-2 py-0.5 rounded">
                              {tag}
                            </span>
                          ))}
                          {template.env_vars.length > 0 && (
                            <span className="text-xs bg-orange-500/20 text-orange-400 px-2 py-0.5 rounded">
                              Needs config
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Basic Info Form */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Agent Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className="w-full p-2 border border-border rounded-md bg-background"
                    placeholder="My Awesome Agent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Model</label>
                  <select
                    value={formData.model_name}
                    onChange={(e) => handleInputChange('model_name', e.target.value)}
                    className="w-full p-2 border border-border rounded-md bg-background"
                  >
                    {availableModels.length > 0 ? (
                      availableModels.map(model => (
                        <option key={model} value={model}>{model}</option>
                      ))
                    ) : (
                      <option value="llama3.2">llama3.2</option>
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Category</label>
                  <select
                    value={formData.category}
                    onChange={(e) => handleInputChange('category', e.target.value)}
                    className="w-full p-2 border border-border rounded-md bg-background"
                  >
                    <option value="">Select a category</option>
                    {availableCategories.map(category => (
                      <option key={category} value={category}>
                        {category.charAt(0).toUpperCase() + category.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Icon</label>
                  <div className="flex items-center gap-2">
                    <select
                      value={formData.icon}
                      onChange={(e) => handleInputChange('icon', e.target.value)}
                      className="flex-1 p-2 border border-border rounded-md bg-background"
                    >
                      {availableIcons.map(icon => (
                        <option key={icon} value={icon}>{icon} {icon}</option>
                      ))}
                    </select>
                    <div className="w-10 h-10 border border-border rounded-md flex items-center justify-center text-xl">
                      {formData.icon}
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  className="w-full p-2 border border-border rounded-md bg-background"
                  rows={3}
                  placeholder="Describe what this agent does..."
                />
              </div>

              {/* Tags */}
              <div>
                <label className="block text-sm font-medium mb-2">Tags</label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {formData.tags.map(tag => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 bg-accent/30 text-muted-foreground px-2 py-1 rounded text-sm"
                    >
                      {tag}
                      <button
                        onClick={() => removeTag(tag)}
                        className="text-muted-foreground hover:text-foreground"
                      >
                        <X size={12} />
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addTag()}
                    className="flex-1 p-2 border border-border rounded-md bg-background"
                    placeholder="Add a tag..."
                  />
                  <button
                    onClick={addTag}
                    className="px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>
          )}

          {currentTab === 'mcp' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">MCP Servers</h3>
                  <p className="text-sm text-muted-foreground">Configure external tool integrations</p>
                </div>
                <button
                  onClick={addMCPServer}
                  className="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                >
                  <Plus size={16} />
                  Add Server
                </button>
              </div>

              {formData.mcp_servers.length === 0 ? (
                <div className="text-center py-8 border-2 border-dashed border-border rounded-lg">
                  <p className="text-muted-foreground mb-4">No MCP servers configured</p>
                  <p className="text-sm text-muted-foreground mb-4">
                    Add MCP servers to give your agent access to external tools and services
                  </p>
                  <button
                    onClick={() => setShowTemplates(true)}
                    className="text-primary hover:underline"
                  >
                    Browse server templates
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {formData.mcp_servers.map((server, index) => (
                    <div key={index} className="p-4 border border-border rounded-lg">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-medium">Server {index + 1}</h4>
                        <button
                          onClick={() => removeMCPServer(index)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-1">Name</label>
                          <input
                            type="text"
                            value={server.name}
                            onChange={(e) => updateMCPServer(index, { name: e.target.value })}
                            className="w-full p-2 border border-border rounded-md bg-background"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-1">Transport</label>
                          <select
                            value={server.transport}
                            onChange={(e) => updateMCPServer(index, { transport: e.target.value as any })}
                            className="w-full p-2 border border-border rounded-md bg-background"
                          >
                            <option value="stdio">stdio (Local command)</option>
                            <option value="sse">SSE (Server-Sent Events)</option>
                            <option value="streamable-http">Streamable HTTP</option>
                          </select>
                        </div>

                        {server.transport === 'stdio' ? (
                          <div className="md:col-span-2">
                            <label className="block text-sm font-medium mb-1">Command *</label>
                            <input
                              type="text"
                              value={server.command || ''}
                              onChange={(e) => updateMCPServer(index, { command: e.target.value })}
                              className="w-full p-2 border border-border rounded-md bg-background"
                              placeholder="npx -y @modelcontextprotocol/server-filesystem ."
                            />
                          </div>
                        ) : (
                          <div className="md:col-span-2">
                            <label className="block text-sm font-medium mb-1">URL *</label>
                            <input
                              type="text"
                              value={server.url || ''}
                              onChange={(e) => updateMCPServer(index, { url: e.target.value })}
                              className="w-full p-2 border border-border rounded-md bg-background"
                              placeholder="http://localhost:8000/sse"
                            />
                          </div>
                        )}

                        <div className="md:col-span-2">
                          <label className="block text-sm font-medium mb-1">Description</label>
                          <input
                            type="text"
                            value={server.description || ''}
                            onChange={(e) => updateMCPServer(index, { description: e.target.value })}
                            className="w-full p-2 border border-border rounded-md bg-background"
                            placeholder="What this server provides..."
                          />
                        </div>
                      </div>

                      <div className="mt-4 flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={server.enabled}
                          onChange={(e) => updateMCPServer(index, { enabled: e.target.checked })}
                          className="rounded"
                        />
                        <label className="text-sm">Enabled</label>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {currentTab === 'advanced' && (
            <div className="space-y-6">
              {/* Instructions */}
              <div>
                <label className="block text-sm font-medium mb-2">Instructions *</label>
                <div className="space-y-2 mb-2">
                  {formData.instructions.map((instruction, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        value={instruction}
                        onChange={(e) => {
                          const updated = [...formData.instructions]
                          updated[index] = e.target.value
                          handleInputChange('instructions', updated)
                        }}
                        className="flex-1 p-2 border border-border rounded-md bg-background"
                      />
                      {formData.instructions.length > 1 && (
                        <button
                          onClick={() => removeInstruction(index)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newInstruction}
                    onChange={(e) => setNewInstruction(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addInstruction()}
                    className="flex-1 p-2 border border-border rounded-md bg-background"
                    placeholder="Add an instruction..."
                  />
                  <button
                    onClick={addInstruction}
                    className="px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                  >
                    Add
                  </button>
                </div>
              </div>

              {/* Welcome Message */}
              <div>
                <label className="block text-sm font-medium mb-2">Welcome Message</label>
                <textarea
                  value={formData.welcome_message}
                  onChange={(e) => handleInputChange('welcome_message', e.target.value)}
                  className="w-full p-2 border border-border rounded-md bg-background"
                  rows={2}
                  placeholder="A message shown to users when they first interact with the agent..."
                />
              </div>

              {/* Example Prompts */}
              <div>
                <label className="block text-sm font-medium mb-2">Example Prompts</label>
                <div className="space-y-2 mb-2">
                  {formData.example_prompts.map((prompt, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        value={prompt}
                        onChange={(e) => {
                          const updated = [...formData.example_prompts]
                          updated[index] = e.target.value
                          handleInputChange('example_prompts', updated)
                        }}
                        className="flex-1 p-2 border border-border rounded-md bg-background"
                      />
                      <button
                        onClick={() => removePrompt(prompt)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newPrompt}
                    onChange={(e) => setNewPrompt(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && addPrompt()}
                    className="flex-1 p-2 border border-border rounded-md bg-background"
                    placeholder="Add an example prompt..."
                  />
                  <button
                    onClick={addPrompt}
                    className="px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                  >
                    Add
                  </button>
                </div>
              </div>

              {/* Behavior Settings */}
              <div>
                <h4 className="font-medium mb-3">Behavior Settings</h4>
                <div className="space-y-3">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.markdown}
                      onChange={(e) => handleInputChange('markdown', e.target.checked)}
                      className="rounded"
                    />
                    <span className="text-sm">Use markdown formatting</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.show_tool_calls}
                      onChange={(e) => handleInputChange('show_tool_calls', e.target.checked)}
                      className="rounded"
                    />
                    <span className="text-sm">Show tool calls to users</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={formData.add_datetime_to_instructions}
                      onChange={(e) => handleInputChange('add_datetime_to_instructions', e.target.checked)}
                      className="rounded"
                    />
                    <span className="text-sm">Add current datetime to instructions</span>
                  </label>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-border">
          <div className="text-sm text-muted-foreground">
            {currentTab === 'basic' && 'Configure basic agent information'}
            {currentTab === 'mcp' && `${formData.mcp_servers.length} MCP server${formData.mcp_servers.length !== 1 ? 's' : ''} configured`}
            {currentTab === 'advanced' && 'Fine-tune agent behavior and examples'}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 text-muted-foreground hover:text-foreground transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <CheckCircle size={16} />
                  Create Agent
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CreateMCPAgentModal 