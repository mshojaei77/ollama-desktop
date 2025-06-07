import React, { useState, useEffect } from 'react'
import { X, Plus, Trash2, Save, AlertTriangle } from 'lucide-react'
import { MCPAgent, MCPServerConfig, UpdateMCPAgentRequest } from '../services/mcpAgentService'

interface EditMCPAgentModalProps {
  agent: MCPAgent
  onClose: () => void
  onSave: (agentId: string, updates: UpdateMCPAgentRequest) => Promise<void>
}

const EditMCPAgentModal: React.FC<EditMCPAgentModalProps> = ({
  agent,
  onClose,
  onSave
}) => {
  const [isSaving, setIsSaving] = useState(false)
  const [formData, setFormData] = useState<UpdateMCPAgentRequest>({
    name: agent.name,
    description: agent.description,
    instructions: [...agent.instructions],
    model_name: agent.model_name,
    model_provider: agent.model_provider,
    mcp_servers: agent.mcp_servers.map(server => ({ ...server })),
    tags: [...agent.tags],
    category: agent.category || '',
    icon: agent.icon,
    example_prompts: [...agent.example_prompts],
    welcome_message: agent.welcome_message || '',
    markdown: agent.markdown,
    show_tool_calls: agent.show_tool_calls,
    add_datetime_to_instructions: agent.add_datetime_to_instructions,
    is_active: agent.is_active
  })

  const handleSave = async () => {
    if (!formData.name?.trim()) {
      alert('Agent name is required')
      return
    }

    setIsSaving(true)
    try {
      await onSave(agent.id, formData)
      onClose()
    } catch (error) {
      console.error('Error saving agent:', error)
      alert('Failed to save agent. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  // Instructions management
  const addInstruction = () => {
    setFormData(prev => ({
      ...prev,
      instructions: [...prev.instructions!, '']
    }))
  }

  const removeInstruction = (index: number) => {
    if (formData.instructions!.length > 1) {
      setFormData(prev => ({
        ...prev,
        instructions: prev.instructions!.filter((_, i) => i !== index)
      }))
    }
  }

  const updateInstruction = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      instructions: prev.instructions!.map((inst, i) => i === index ? value : inst)
    }))
  }

  // Tags management
  const addTag = () => {
    setFormData(prev => ({
      ...prev,
      tags: [...prev.tags!, '']
    }))
  }

  const removeTag = (index: number) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags!.filter((_, i) => i !== index)
    }))
  }

  const updateTag = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags!.map((tag, i) => i === index ? value : tag)
    }))
  }

  // Example prompts management
  const addExamplePrompt = () => {
    setFormData(prev => ({
      ...prev,
      example_prompts: [...prev.example_prompts!, '']
    }))
  }

  const removeExamplePrompt = (index: number) => {
    setFormData(prev => ({
      ...prev,
      example_prompts: prev.example_prompts!.filter((_, i) => i !== index)
    }))
  }

  const updateExamplePrompt = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      example_prompts: prev.example_prompts!.map((prompt, i) => i === index ? value : prompt)
    }))
  }

  // MCP Servers management
  const addMCPServer = () => {
    const newServer: MCPServerConfig = {
      name: '',
      transport: 'stdio',
      command: '',
      args: [],
      env: {},
      enabled: true,
      description: ''
    }
    setFormData(prev => ({
      ...prev,
      mcp_servers: [...prev.mcp_servers!, newServer]
    }))
  }

  const removeMCPServer = (index: number) => {
    setFormData(prev => ({
      ...prev,
      mcp_servers: prev.mcp_servers!.filter((_, i) => i !== index)
    }))
  }

  const updateMCPServer = (index: number, updates: Partial<MCPServerConfig>) => {
    setFormData(prev => ({
      ...prev,
      mcp_servers: prev.mcp_servers!.map((server, i) => 
        i === index ? { ...server, ...updates } : server
      )
    }))
  }

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-lg">
        <div className="sticky top-0 bg-[hsl(var(--card))] border-b border-[hsl(var(--border))] p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-[hsl(var(--foreground))] flex items-center gap-2">
              Edit Agent: {agent.name}
            </h2>
            <button
              onClick={onClose}
              className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] p-1 rounded transition-colors"
              disabled={isSaving}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-[hsl(var(--foreground))]">Basic Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  value={formData.name || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 bg-[hsl(var(--background))] border border-[hsl(var(--border))] rounded text-[hsl(var(--foreground))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--primary))]"
                  disabled={isSaving}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1">
                  Category
                </label>
                <input
                  type="text"
                  value={formData.category || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 bg-[hsl(var(--background))] border border-[hsl(var(--border))] rounded text-[hsl(var(--foreground))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--primary))]"
                  disabled={isSaving}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1">
                Description
              </label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3 py-2 bg-[hsl(var(--background))] border border-[hsl(var(--border))] rounded text-[hsl(var(--foreground))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--primary))]"
                rows={3}
                disabled={isSaving}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1">
                  Model Provider
                </label>
                <input
                  type="text"
                  value={formData.model_provider || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, model_provider: e.target.value }))}
                  className="w-full px-3 py-2 bg-[hsl(var(--background))] border border-[hsl(var(--border))] rounded text-[hsl(var(--foreground))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--primary))]"
                  disabled={isSaving}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1">
                  Model Name
                </label>
                <input
                  type="text"
                  value={formData.model_name || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, model_name: e.target.value }))}
                  className="w-full px-3 py-2 bg-[hsl(var(--background))] border border-[hsl(var(--border))] rounded text-[hsl(var(--foreground))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--primary))]"
                  disabled={isSaving}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1">
                  Icon
                </label>
                <input
                  type="text"
                  value={formData.icon || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, icon: e.target.value }))}
                  className="w-full px-3 py-2 bg-[hsl(var(--background))] border border-[hsl(var(--border))] rounded text-[hsl(var(--foreground))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--primary))]"
                  placeholder="🤖 or URL"
                  disabled={isSaving}
                />
              </div>
            </div>
          </div>

          {/* Instructions */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-[hsl(var(--foreground))]">Instructions</h3>
              <button
                onClick={addInstruction}
                className="flex items-center gap-1 px-2 py-1 text-sm bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] rounded hover:bg-[hsl(var(--primary))]/90 transition-colors"
                disabled={isSaving}
              >
                <Plus size={14} />
                Add
              </button>
            </div>
            
            {formData.instructions?.map((instruction, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="text"
                  value={instruction}
                  onChange={(e) => updateInstruction(index, e.target.value)}
                  className="flex-1 px-3 py-2 bg-[hsl(var(--background))] border border-[hsl(var(--border))] rounded text-[hsl(var(--foreground))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--primary))]"
                  placeholder="Enter instruction..."
                  disabled={isSaving}
                />
                {formData.instructions!.length > 1 && (
                  <button
                    onClick={() => removeInstruction(index)}
                    className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded transition-colors"
                    disabled={isSaving}
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Tags */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-[hsl(var(--foreground))]">Tags</h3>
              <button
                onClick={addTag}
                className="flex items-center gap-1 px-2 py-1 text-sm bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] rounded hover:bg-[hsl(var(--primary))]/90 transition-colors"
                disabled={isSaving}
              >
                <Plus size={14} />
                Add
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
              {formData.tags?.map((tag, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={tag}
                    onChange={(e) => updateTag(index, e.target.value)}
                    className="flex-1 px-3 py-2 bg-[hsl(var(--background))] border border-[hsl(var(--border))] rounded text-[hsl(var(--foreground))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--primary))]"
                    placeholder="Tag name"
                    disabled={isSaving}
                  />
                  <button
                    onClick={() => removeTag(index)}
                    className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded transition-colors"
                    disabled={isSaving}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-[hsl(var(--foreground))]">Settings</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1">
                  Welcome Message
                </label>
                <textarea
                  value={formData.welcome_message || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, welcome_message: e.target.value }))}
                  className="w-full px-3 py-2 bg-[hsl(var(--background))] border border-[hsl(var(--border))] rounded text-[hsl(var(--foreground))] focus:outline-none focus:ring-1 focus:ring-[hsl(var(--primary))]"
                  rows={2}
                  disabled={isSaving}
                />
              </div>
              
              <div className="space-y-3">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.markdown || false}
                    onChange={(e) => setFormData(prev => ({ ...prev, markdown: e.target.checked }))}
                    className="rounded"
                    disabled={isSaving}
                  />
                  <span className="text-sm text-[hsl(var(--foreground))]">Use Markdown formatting</span>
                </label>
                
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.show_tool_calls || false}
                    onChange={(e) => setFormData(prev => ({ ...prev, show_tool_calls: e.target.checked }))}
                    className="rounded"
                    disabled={isSaving}
                  />
                  <span className="text-sm text-[hsl(var(--foreground))]">Show tool calls</span>
                </label>
                
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.add_datetime_to_instructions || false}
                    onChange={(e) => setFormData(prev => ({ ...prev, add_datetime_to_instructions: e.target.checked }))}
                    className="rounded"
                    disabled={isSaving}
                  />
                  <span className="text-sm text-[hsl(var(--foreground))]">Add date/time to instructions</span>
                </label>
                
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active || false}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="rounded"
                    disabled={isSaving}
                  />
                  <span className="text-sm text-[hsl(var(--foreground))]">Agent is active</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-[hsl(var(--card))] border-t border-[hsl(var(--border))] p-6">
          <div className="flex gap-3 justify-end">
            <button
              onClick={onClose}
              disabled={isSaving}
              className="px-4 py-2 border border-[hsl(var(--border))] rounded-md text-[hsl(var(--foreground))] hover:bg-[hsl(var(--accent))]/20 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || !formData.name?.trim()}
              className="px-4 py-2 bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] rounded-md hover:bg-[hsl(var(--primary))]/90 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save size={16} />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default EditMCPAgentModal 