import { useState, useEffect } from 'react'
import { ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function Settings(): JSX.Element {
  const [theme, setTheme] = useState<string>('system')
  const navigate = useNavigate()

  // Load theme preference from local storage on component mount
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'system'
    setTheme(savedTheme)
    applyTheme(savedTheme)
  }, [])

  // Apply the selected theme to the document
  const applyTheme = (selectedTheme: string): void => {
    const root = window.document.documentElement
    
    // Remove any existing theme class
    root.classList.remove('dark', 'light')
    
    if (selectedTheme === 'system') {
      // Check system preference
      const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      systemPrefersDark ? root.classList.add('dark') : root.classList.add('light')
    } else {
      // Apply the selected theme directly
      root.classList.add(selectedTheme)
    }
  }

  const handleThemeChange = (newTheme: string): void => {
    setTheme(newTheme)
    applyTheme(newTheme)
    // Save settings to local storage immediately
    localStorage.setItem('theme', newTheme)
    console.log('Theme changed to:', newTheme)
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
      </div>
    </div>
  )
}
