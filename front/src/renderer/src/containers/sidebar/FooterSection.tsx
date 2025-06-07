import { Settings, Bot, Layers } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Routes } from '../../lib/routes'

const FooterSection = (): JSX.Element => {
  const navigate = useNavigate()

  return (
    <div className="p-2 space-y-1 border-t border-[hsl(var(--border))]">
      <div 
        className="flex items-center p-2 rounded-lg cursor-pointer hover:bg-[hsl(var(--secondary))]"
        onClick={() => navigate(Routes.AGENTS)}
      >
        <Bot className="h-4 w-4 mr-2 text-[hsl(var(--muted-foreground))]" />
        <span className="text-sm text-[hsl(var(--foreground))]">Agents</span>
      </div>
      <div
        className="flex items-center p-2 rounded-lg cursor-pointer hover:bg-[hsl(var(--secondary))]"
        onClick={() => navigate('/models')}
      >
        <Layers className="h-4 w-4 mr-2 text-[hsl(var(--muted-foreground))]" />
        <span className="text-sm text-[hsl(var(--foreground))]">Models</span>
      </div>
      <div 
        className="flex items-center p-2 rounded-lg cursor-pointer hover:bg-[hsl(var(--secondary))]"
        onClick={() => navigate('/settings')}
      >
        <Settings className="h-4 w-4 mr-2 text-[hsl(var(--muted-foreground))]" />
        <span className="text-sm text-[hsl(var(--foreground))]">Settings</span>
      </div>
    </div>
  )
}

export default FooterSection
