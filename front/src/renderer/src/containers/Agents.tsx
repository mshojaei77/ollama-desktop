import { useState } from 'react'
import { Search, ChevronDown } from 'lucide-react'

type Agent = {
  id: string
  name: string
  description: string
  icon: string
  tags: string[]
}

const mockAgents: Agent[] = [
  {
    id: '1',
    name: 'AssistantPro',
    description: 'AssistantPro is an AI model like no other. With no restrictions, filters, or guardrails.',
    icon: 'https://picsum.photos/200',
    tags: ['general']
  },
  {
    id: '4',
    name: 'ImageCraft Studio',
    description: 'Generate Images in HD, BULK and With Simple Prompts for FREE.',
    icon: 'https://picsum.photos/203',
    tags: ['image']
  }
]

function Agents(): JSX.Element {
  const [filter, setFilter] = useState('')
  const [selectedTag, setSelectedTag] = useState('')

  const filteredAgents = mockAgents.filter(agent => 
    agent.name.toLowerCase().includes(filter.toLowerCase()) ||
    agent.description.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <div className="flex flex-col h-full p-6 bg-background overflow-auto">
      <div className="flex flex-col mb-6">
        <div className="flex items-center mb-4">
          <h1 className="text-2xl font-semibold text-foreground">Agents <span className="text-xs bg-accent/20 text-muted-foreground px-1 rounded ml-1">BETA</span></h1>
        </div>
        <p className="text-muted-foreground text-sm">Supercharge your workflow with AI agents tailored to your exact needs</p>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <div className="relative">
            <select className="bg-background border border-border rounded-md pl-3 pr-8 py-1 text-sm text-foreground appearance-none focus:outline-none focus:ring-1 focus:ring-primary [&>option]:!bg-[#1e1e2f] dark:[&>option]:!bg-[#1e1e2f] [&>option]:!text-foreground">
              <option>All models</option>
              <option>Local models</option>
              <option>Remote models</option>
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-muted-foreground">
              <ChevronDown className="h-4 w-4" />
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className="relative">
            <input
              type="text"
              placeholder="Filter by name"
              className="bg-background border border-border rounded-md pl-8 pr-3 py-1 text-sm"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
            <Search className="h-4 w-4 text-muted-foreground absolute left-2 top-1/2 transform -translate-y-1/2" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {filteredAgents.map(agent => (
          <div key={agent.id} className="bg-card border border-border rounded-lg overflow-hidden flex flex-col">
            <div className="flex items-center space-x-4 p-4">
              <div className="flex-shrink-0">
                <img src={agent.icon} alt={agent.name} className="w-12 h-12 rounded-full object-cover" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-foreground font-medium truncate">{agent.name}</p>
              </div>
            </div>
            <div className="p-4 flex-1">
              <p className="text-sm text-muted-foreground mb-4">{agent.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Agents
