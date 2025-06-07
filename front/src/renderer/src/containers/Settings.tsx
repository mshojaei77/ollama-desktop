import { useState, useEffect } from 'react'
import { ArrowLeft, Plus, Edit, Trash2, Check, X, Save } from 'lucide-react'
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
  const navigate = useNavigate()

  // Load settings on component mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'system'
    setTheme(savedTheme)
    applyTheme(savedTheme)
    loadSystemPrompts()
  }, [])

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
    setTheme(newTheme)
    applyTheme(newTheme)
    localStorage.setItem('theme', newTheme)
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
        <h1 className="text-2xl font-bold">Settings</h1>
      </div>

      <div className="grid gap-6 md:grid-cols-1">
        {/* Appearance Settings */}
        <div className="border border-[hsl(var(--border))] rounded-lg p-6 shadow-sm bg-[hsl(var(--card))]">
          <div className="flex flex-col space-y-1.5 mb-4">
            <h3 className="text-lg font-semibold">Appearance</h3>
            <p className="text-sm text-[hsl(var(--muted-foreground))]">Customize how Ollama Desktop looks</p>
          </div>
          <div className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="theme" className="text-sm font-medium">Theme</label>
              <select 
                id="theme"
                value={theme}
                onChange={(e) => handleThemeChange(e.target.value)}
                className="w-full h-9 rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--background))] px-3 py-2 text-sm"
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="system">System</option>
              </select>
            </div>
          </div>
        </div>

        {/* System Prompts Settings */}
        <div className="border border-[hsl(var(--border))] rounded-lg p-6 shadow-sm bg-[hsl(var(--card))]">
          <div className="flex flex-col space-y-1.5 mb-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">System Prompts</h3>
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
      </div>
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
