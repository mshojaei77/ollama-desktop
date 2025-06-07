import { useState, useEffect } from 'react'
import { ArrowLeft, Plus, Edit, Trash2, Check, X, Save, RefreshCw, Settings as SettingsIcon, Palette, Cpu, MessageSquare, Database } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Textarea } from '../components/ui/textarea'
import { toast } from 'sonner'

interface SystemPromptConfig {
  name: string
  description: string
  instructions: string[]
  additional_context: string
  expected_output: string
  markdown: boolean
  add_datetime_to_instructions: boolean
}

interface SystemPrompt {
  id: string
  config: SystemPromptConfig
}

interface SystemPromptsResponse {
  prompts: SystemPrompt[]
  active_prompt_id: string
}

interface SettingsConfig {
  base_url: string
  default_model: string
  temperature: number
  top_p: number
  active_system_prompt_id: string
  theme: string
  auto_save_chats: boolean
  max_chat_history: number
}

interface SettingsResponse {
  config: SettingsConfig
  status: string
}

export default function Settings(): JSX.Element {
  const [theme, setTheme] = useState<string>('system')
  const [systemPrompts, setSystemPrompts] = useState<SystemPrompt[]>([])
  const [activePromptId, setActivePromptId] = useState<string>('default')
  const [editingPrompt, setEditingPrompt] = useState<string | null>(null)
  const [newPrompt, setNewPrompt] = useState<SystemPromptConfig>({
    name: '',
    description: '',
    instructions: [''],
    additional_context: '',
    expected_output: '',
    markdown: true,
    add_datetime_to_instructions: false
  })
  const [isCreating, setIsCreating] = useState(false)
  const [loading, setLoading] = useState(true)
  const [settingsLoading, setSettingsLoading] = useState(false)
  
  // New settings state
  const [settings, setSettings] = useState<SettingsConfig>({
    base_url: 'http://localhost:11434',
    default_model: 'llama3.2',
    temperature: 0.7,
    top_p: 0.9,
    active_system_prompt_id: 'default',
    theme: 'system',
    auto_save_chats: true,
    max_chat_history: 1000
  })
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [activeTab, setActiveTab] = useState<'general' | 'prompts' | 'advanced'>('general')
  
  const navigate = useNavigate()

  // Load settings on component mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'system'
    setTheme(savedTheme)
    applyTheme(savedTheme)
    loadSettings()
    loadSystemPrompts()
    loadAvailableModels()
  }, [])

  const loadSettings = async () => {
    try {
      setSettingsLoading(true)
      const response = await fetch('http://localhost:8000/settings')
      if (!response.ok) throw new Error('Failed to fetch settings')
      
      const data: SettingsResponse = await response.json()
      setSettings(data.config)
      setTheme(data.config.theme)
      applyTheme(data.config.theme)
    } catch (error) {
      console.error('Error loading settings:', error)
      toast.error('Failed to load settings')
    } finally {
      setSettingsLoading(false)
    }
  }

  const loadSystemPrompts = async () => {
    try {
      const response = await fetch('http://localhost:8000/system-prompts')
      if (!response.ok) throw new Error('Failed to fetch system prompts')
      
      const data: SystemPromptsResponse = await response.json()
      setSystemPrompts(data.prompts)
      setActivePromptId(data.active_prompt_id)
    } catch (error) {
      console.error('Error loading system prompts:', error)
      toast.error('Failed to load system prompts')
    } finally {
      setLoading(false)
    }
  }

  const loadAvailableModels = async () => {
    try {
      const response = await fetch('http://localhost:8000/available-models')
      if (!response.ok) throw new Error('Failed to fetch models')
      
      const data = await response.json()
      setAvailableModels(data.models || [])
    } catch (error) {
      console.error('Error loading models:', error)
      // Don't show error toast for models as it's not critical
    }
  }

  const updateSettings = async (updates: Partial<SettingsConfig>) => {
    try {
      setSettingsLoading(true)
      const response = await fetch('http://localhost:8000/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to update settings')
      }
      
      const data: SettingsResponse = await response.json()
      setSettings(data.config)
      
      // Update theme if it was changed
      if (updates.theme) {
        setTheme(updates.theme)
        applyTheme(updates.theme)
        localStorage.setItem('theme', updates.theme)
      }
      
      toast.success('Settings updated successfully')
    } catch (error) {
      console.error('Error updating settings:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to update settings')
    } finally {
      setSettingsLoading(false)
    }
  }

  const resetSettings = async () => {
    try {
      setSettingsLoading(true)
      const response = await fetch('http://localhost:8000/settings/reset', {
        method: 'POST'
      })
      
      if (!response.ok) throw new Error('Failed to reset settings')
      
      const data: SettingsResponse = await response.json()
      setSettings(data.config)
      setTheme(data.config.theme)
      applyTheme(data.config.theme)
      localStorage.setItem('theme', data.config.theme)
      
      toast.success('Settings reset to defaults')
    } catch (error) {
      console.error('Error resetting settings:', error)
      toast.error('Failed to reset settings')
    } finally {
      setSettingsLoading(false)
    }
  }

  const applyTheme = (selectedTheme: string): void => {
    const root = window.document.documentElement
    root.classList.remove('dark', 'light')
    
    if (selectedTheme === 'system') {
      const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      systemPrefersDark ? root.classList.add('dark') : root.classList.add('light')
    } else {
      root.classList.add(selectedTheme)
    }
  }

  const handleThemeChange = (newTheme: string): void => {
    updateSettings({ theme: newTheme })
  }

  const setActivePrompt = async (promptId: string) => {
    try {
      const response = await fetch('http://localhost:8000/system-prompts/active', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt_id: promptId })
      })
      
      if (!response.ok) throw new Error('Failed to set active prompt')
      
      setActivePromptId(promptId)
      // Also update the settings to reflect the change
      await updateSettings({ active_system_prompt_id: promptId })
      toast.success(`Activated "${systemPrompts.find(p => p.id === promptId)?.config.name}" prompt`)
    } catch (error) {
      console.error('Error setting active prompt:', error)
      toast.error('Failed to set active prompt')
    }
  }

  const savePrompt = async (promptId: string, config: SystemPromptConfig) => {
    try {
      const response = await fetch('http://localhost:8000/system-prompts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt_id: promptId, config })
      })
      
      if (!response.ok) throw new Error('Failed to save prompt')
      
      await loadSystemPrompts()
      setEditingPrompt(null)
      toast.success(`Saved "${config.name}" prompt`)
    } catch (error) {
      console.error('Error saving prompt:', error)
      toast.error('Failed to save prompt')
    }
  }

  const deletePrompt = async (promptId: string) => {
    if (promptId === 'default') {
      toast.error('Cannot delete the default prompt')
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/system-prompts/${promptId}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) throw new Error('Failed to delete prompt')
      
      await loadSystemPrompts()
      toast.success('Prompt deleted successfully')
    } catch (error) {
      console.error('Error deleting prompt:', error)
      toast.error('Failed to delete prompt')
    }
  }

  const createNewPrompt = async () => {
    if (!newPrompt.name.trim()) {
      toast.error('Please enter a prompt name')
      return
    }

    const promptId = newPrompt.name.toLowerCase().replace(/[^a-z0-9]/g, '_')
    await savePrompt(promptId, newPrompt)
    
    setNewPrompt({
      name: '',
      description: '',
      instructions: [''],
      additional_context: '',
      expected_output: '',
      markdown: true,
      add_datetime_to_instructions: false
    })
    setIsCreating(false)
  }

  const addInstruction = (promptConfig: SystemPromptConfig, setConfig: (config: SystemPromptConfig) => void) => {
    setConfig({
      ...promptConfig,
      instructions: [...promptConfig.instructions, '']
    })
  }

  const removeInstruction = (index: number, promptConfig: SystemPromptConfig, setConfig: (config: SystemPromptConfig) => void) => {
    if (promptConfig.instructions.length > 1) {
      setConfig({
        ...promptConfig,
        instructions: promptConfig.instructions.filter((_, i) => i !== index)
      })
    }
  }

  const updateInstruction = (index: number, value: string, promptConfig: SystemPromptConfig, setConfig: (config: SystemPromptConfig) => void) => {
    const newInstructions = [...promptConfig.instructions]
    newInstructions[index] = value
    setConfig({
      ...promptConfig,
      instructions: newInstructions
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full max-h-screen bg-[hsl(var(--background))] p-6 overflow-y-auto">
      <div className="flex items-center mb-6">
        <button 
          onClick={() => navigate(-1)}
          className="mr-2 p-2 rounded-full hover:bg-[hsl(var(--secondary))]"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <SettingsIcon className="h-6 w-6" />
          Settings
        </h1>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 mb-6 bg-[hsl(var(--muted))] p-1 rounded-lg">
        <button
          onClick={() => setActiveTab('general')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'general'
              ? 'bg-[hsl(var(--background))] text-[hsl(var(--foreground))] shadow-sm'
              : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
          }`}
        >
          <Palette className="h-4 w-4" />
          General
        </button>
        <button
          onClick={() => setActiveTab('prompts')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'prompts'
              ? 'bg-[hsl(var(--background))] text-[hsl(var(--foreground))] shadow-sm'
              : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
          }`}
        >
          <MessageSquare className="h-4 w-4" />
          System Prompts
        </button>
        <button
          onClick={() => setActiveTab('advanced')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'advanced'
              ? 'bg-[hsl(var(--background))] text-[hsl(var(--foreground))] shadow-sm'
              : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
          }`}
        >
          <Cpu className="h-4 w-4" />
          Advanced
        </button>
      </div>

      {/* General Settings Tab */}
      {activeTab === 'general' && (
        <div className="space-y-6">
          {/* Appearance Settings */}
          <div className="border border-[hsl(var(--border))] rounded-lg p-6 shadow-sm bg-[hsl(var(--card))]">
            <div className="flex flex-col space-y-1.5 mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Appearance
              </h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">Customize how Ollama Desktop looks</p>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="theme" className="text-sm font-medium">Theme</label>
                <select 
                  id="theme"
                  value={settings.theme}
                  onChange={(e) => handleThemeChange(e.target.value)}
                  disabled={settingsLoading}
                  className="w-full h-9 rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3 py-2 text-sm disabled:opacity-50"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="system">System</option>
                </select>
              </div>
            </div>
          </div>

          {/* Connection Settings */}
          <div className="border border-[hsl(var(--border))] rounded-lg p-6 shadow-sm bg-[hsl(var(--card))]">
            <div className="flex flex-col space-y-1.5 mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Database className="h-5 w-5" />
                Connection
              </h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">Configure Ollama server connection</p>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="base_url" className="text-sm font-medium">Base URL</label>
                <div className="flex gap-2">
                  <Input
                    id="base_url"
                    value={settings.base_url}
                    onChange={(e) => setSettings({ ...settings, base_url: e.target.value })}
                    placeholder="http://localhost:11434"
                    disabled={settingsLoading}
                  />
                  <Button 
                    onClick={() => updateSettings({ base_url: settings.base_url })}
                    disabled={settingsLoading}
                    size="sm"
                  >
                    {settingsLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                  </Button>
                </div>
                <p className="text-xs text-[hsl(var(--muted-foreground))]">
                  URL of your Ollama server (e.g., http://localhost:11434)
                </p>
              </div>
            </div>
          </div>

          {/* Model Settings */}
          <div className="border border-[hsl(var(--border))] rounded-lg p-6 shadow-sm bg-[hsl(var(--card))]">
            <div className="flex flex-col space-y-1.5 mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Cpu className="h-5 w-5" />
                Default Model
              </h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">Choose the default model for new conversations</p>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="default_model" className="text-sm font-medium">Model</label>
                <div className="flex gap-2">
                  <select 
                    id="default_model"
                    value={settings.default_model}
                    onChange={(e) => setSettings({ ...settings, default_model: e.target.value })}
                    disabled={settingsLoading}
                    className="flex-1 h-9 rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3 py-2 text-sm disabled:opacity-50"
                  >
                    {availableModels.length > 0 ? (
                      availableModels.map(model => (
                        <option key={model} value={model}>{model}</option>
                      ))
                    ) : (
                      <option value={settings.default_model}>{settings.default_model}</option>
                    )}
                  </select>
                  <Button 
                    onClick={() => updateSettings({ default_model: settings.default_model })}
                    disabled={settingsLoading}
                    size="sm"
                  >
                    {settingsLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* System Prompts Tab */}
      {activeTab === 'prompts' && (
        <div className="border border-[hsl(var(--border))] rounded-lg p-6 shadow-sm bg-[hsl(var(--card))]">
          <div className="flex flex-col space-y-1.5 mb-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  System Prompts
                </h3>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Manage AI assistant behavior and personality</p>
              </div>
              <Button 
                onClick={() => setIsCreating(true)}
                size="sm"
                className="flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                New Prompt
              </Button>
            </div>
          </div>

          <div className="space-y-4">
            {/* Create New Prompt Form */}
            {isCreating && (
              <div className="border rounded-lg p-4 bg-[hsl(var(--muted))] space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">Create New Prompt</h4>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={createNewPrompt}>
                      <Save className="h-4 w-4 mr-1" />
                      Save
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setIsCreating(false)}>
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                
                <div className="grid gap-4">
                  <div>
                    <label className="text-sm font-medium">Name</label>
                    <Input
                      value={newPrompt.name}
                      onChange={(e) => setNewPrompt({ ...newPrompt, name: e.target.value })}
                      placeholder="e.g., Creative Writer"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Description</label>
                    <Input
                      value={newPrompt.description}
                      onChange={(e) => setNewPrompt({ ...newPrompt, description: e.target.value })}
                      placeholder="Brief description of the prompt's purpose"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Instructions</label>
                    {newPrompt.instructions.map((instruction, index) => (
                      <div key={index} className="flex gap-2 mb-2">
                        <Input
                          value={instruction}
                          onChange={(e) => updateInstruction(index, e.target.value, newPrompt, setNewPrompt)}
                          placeholder="Enter an instruction..."
                        />
                        {newPrompt.instructions.length > 1 && (
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => removeInstruction(index, newPrompt, setNewPrompt)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    ))}
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => addInstruction(newPrompt, setNewPrompt)}
                    >
                      <Plus className="h-4 w-4 mr-1" />
                      Add Instruction
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Existing Prompts */}
            {systemPrompts.map((prompt) => (
              <div key={prompt.id} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{prompt.config.name}</h4>
                        {activePromptId === prompt.id && (
                          <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                            Active
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-[hsl(var(--muted-foreground))]">
                        {prompt.config.description}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {activePromptId !== prompt.id && (
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => setActivePrompt(prompt.id)}
                      >
                        <Check className="h-4 w-4 mr-1" />
                        Activate
                      </Button>
                    )}
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => setEditingPrompt(editingPrompt === prompt.id ? null : prompt.id)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    {prompt.id !== 'default' && (
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => deletePrompt(prompt.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>

                {/* Edit Form */}
                {editingPrompt === prompt.id && (
                  <EditPromptForm 
                    prompt={prompt}
                    onSave={(config) => savePrompt(prompt.id, config)}
                    onCancel={() => setEditingPrompt(null)}
                  />
                )}

                {/* Instructions Preview */}
                {editingPrompt !== prompt.id && (
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Instructions:</div>
                    <ul className="text-sm text-[hsl(var(--muted-foreground))] list-disc list-inside space-y-1">
                      {prompt.config.instructions.map((instruction, index) => (
                        <li key={index}>{instruction}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Advanced Settings Tab */}
      {activeTab === 'advanced' && (
        <div className="space-y-6">
          {/* Model Parameters */}
          <div className="border border-[hsl(var(--border))] rounded-lg p-6 shadow-sm bg-[hsl(var(--card))]">
            <div className="flex flex-col space-y-1.5 mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Cpu className="h-5 w-5" />
                Model Parameters
              </h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">Fine-tune model behavior</p>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label htmlFor="temperature" className="text-sm font-medium">
                  Temperature: {settings.temperature}
                </label>
                <input
                  id="temperature"
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={settings.temperature}
                  onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
                  disabled={settingsLoading}
                  className="w-full"
                />
                <p className="text-xs text-[hsl(var(--muted-foreground))]">
                  Controls randomness (0 = deterministic, 2 = very creative)
                </p>
              </div>
              <div className="space-y-2">
                <label htmlFor="top_p" className="text-sm font-medium">
                  Top P: {settings.top_p}
                </label>
                <input
                  id="top_p"
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={settings.top_p}
                  onChange={(e) => setSettings({ ...settings, top_p: parseFloat(e.target.value) })}
                  disabled={settingsLoading}
                  className="w-full"
                />
                <p className="text-xs text-[hsl(var(--muted-foreground))]">
                  Controls diversity of word selection
                </p>
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <Button 
                onClick={() => updateSettings({ 
                  temperature: settings.temperature, 
                  top_p: settings.top_p 
                })}
                disabled={settingsLoading}
                size="sm"
              >
                {settingsLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Save Parameters
              </Button>
            </div>
          </div>

          {/* Chat Management */}
          <div className="border border-[hsl(var(--border))] rounded-lg p-6 shadow-sm bg-[hsl(var(--card))]">
            <div className="flex flex-col space-y-1.5 mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Chat Management
              </h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">Configure chat behavior and storage</p>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium">Auto-save chats</label>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">
                    Automatically save chat history
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={settings.auto_save_chats}
                  onChange={(e) => setSettings({ ...settings, auto_save_chats: e.target.checked })}
                  disabled={settingsLoading}
                  className="rounded"
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="max_history" className="text-sm font-medium">
                  Max chat history: {settings.max_chat_history}
                </label>
                <input
                  id="max_history"
                  type="range"
                  min="100"
                  max="5000"
                  step="100"
                  value={settings.max_chat_history}
                  onChange={(e) => setSettings({ ...settings, max_chat_history: parseInt(e.target.value) })}
                  disabled={settingsLoading}
                  className="w-full"
                />
                <p className="text-xs text-[hsl(var(--muted-foreground))]">
                  Maximum number of messages to keep in history
                </p>
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <Button 
                onClick={() => updateSettings({ 
                  auto_save_chats: settings.auto_save_chats,
                  max_chat_history: settings.max_chat_history
                })}
                disabled={settingsLoading}
                size="sm"
              >
                {settingsLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Save Chat Settings
              </Button>
            </div>
          </div>

          {/* Reset Settings */}
          <div className="border border-red-200 rounded-lg p-6 shadow-sm bg-red-50 dark:bg-red-950 dark:border-red-800">
            <div className="flex flex-col space-y-1.5 mb-4">
              <h3 className="text-lg font-semibold text-red-800 dark:text-red-200">Reset Settings</h3>
              <p className="text-sm text-red-600 dark:text-red-300">
                Reset all settings to their default values. This will not affect saved prompts or chat history.
              </p>
            </div>
            <Button 
              onClick={resetSettings}
              disabled={settingsLoading}
              variant="outline"
              className="border-red-300 text-red-700 hover:bg-red-100 dark:border-red-700 dark:text-red-300 dark:hover:bg-red-900"
            >
              {settingsLoading ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Reset to Defaults
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

// Separate component for editing prompts
function EditPromptForm({ 
  prompt, 
  onSave, 
  onCancel 
}: { 
  prompt: SystemPrompt
  onSave: (config: SystemPromptConfig) => void
  onCancel: () => void
}) {
  const [editConfig, setEditConfig] = useState<SystemPromptConfig>({ ...prompt.config })

  const addInstruction = () => {
    setEditConfig({
      ...editConfig,
      instructions: [...editConfig.instructions, '']
    })
  }

  const removeInstruction = (index: number) => {
    if (editConfig.instructions.length > 1) {
      setEditConfig({
        ...editConfig,
        instructions: editConfig.instructions.filter((_, i) => i !== index)
      })
    }
  }

  const updateInstruction = (index: number, value: string) => {
    const newInstructions = [...editConfig.instructions]
    newInstructions[index] = value
    setEditConfig({
      ...editConfig,
      instructions: newInstructions
    })
  }

  return (
    <div className="border rounded-lg p-4 bg-[hsl(var(--muted))] space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="font-medium">Edit Prompt</h4>
        <div className="flex gap-2">
          <Button size="sm" onClick={() => onSave(editConfig)}>
            <Save className="h-4 w-4 mr-1" />
            Save
          </Button>
          <Button size="sm" variant="outline" onClick={onCancel}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>
      
      <div className="grid gap-4">
        <div>
          <label className="text-sm font-medium">Name</label>
          <Input
            value={editConfig.name}
            onChange={(e) => setEditConfig({ ...editConfig, name: e.target.value })}
          />
        </div>
        <div>
          <label className="text-sm font-medium">Description</label>
          <Input
            value={editConfig.description}
            onChange={(e) => setEditConfig({ ...editConfig, description: e.target.value })}
          />
        </div>
        <div>
          <label className="text-sm font-medium">Instructions</label>
          {editConfig.instructions.map((instruction, index) => (
            <div key={index} className="flex gap-2 mb-2">
              <Input
                value={instruction}
                onChange={(e) => updateInstruction(index, e.target.value)}
                placeholder="Enter an instruction..."
              />
              {editConfig.instructions.length > 1 && (
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => removeInstruction(index)}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          ))}
          <Button 
            size="sm" 
            variant="outline" 
            onClick={addInstruction}
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Instruction
          </Button>
        </div>
        <div>
          <label className="text-sm font-medium">Additional Context (Optional)</label>
          <Textarea
            value={editConfig.additional_context}
            onChange={(e) => setEditConfig({ ...editConfig, additional_context: e.target.value })}
            placeholder="Additional context for the AI..."
            rows={3}
          />
        </div>
        <div>
          <label className="text-sm font-medium">Expected Output (Optional)</label>
          <Textarea
            value={editConfig.expected_output}
            onChange={(e) => setEditConfig({ ...editConfig, expected_output: e.target.value })}
            placeholder="Describe the expected output format..."
            rows={2}
          />
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={editConfig.markdown}
              onChange={(e) => setEditConfig({ ...editConfig, markdown: e.target.checked })}
            />
            <span className="text-sm">Use Markdown formatting</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={editConfig.add_datetime_to_instructions}
              onChange={(e) => setEditConfig({ ...editConfig, add_datetime_to_instructions: e.target.checked })}
            />
            <span className="text-sm">Include current date/time</span>
          </label>
        </div>
      </div>
    </div>
  )
}
