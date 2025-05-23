import { useState, useEffect } from 'react'
import { Search, ChevronDown, Tag, RefreshCw } from 'lucide-react'
import agentService, { Agent } from '../services/agentService'
import AgentChat from '../components/AgentChat'
import { getAgentIconPath } from '../utils'

function Agents(): JSX.Element {
  const [filter, setFilter] = useState('')
  const [selectedTag, setSelectedTag] = useState('')
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [allTags, setAllTags] = useState<string[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)

  // Fetch agents from API
  const fetchAgents = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const agentList = await agentService.getAllAgents()
      setAgents(agentList)
      
      // Extract all unique tags from agents
      const tags = new Set<string>()
      agentList.forEach(agent => {
        agent.tags.forEach(tag => tags.add(tag))
      })
      setAllTags(Array.from(tags).sort())
    } catch (err) {
      console.error('Failed to fetch agents:', err)
      setError('Failed to load agents. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }
  
  // Initial fetch on component mount
  useEffect(() => {
    fetchAgents()
  }, [])

  // Filter agents based on search and tag filter
  const filteredAgents = agents.filter(agent => {
    const matchesSearch = 
      agent.name.toLowerCase().includes(filter.toLowerCase()) ||
      agent.description.toLowerCase().includes(filter.toLowerCase())
    
    const matchesTag = !selectedTag || agent.tags.includes(selectedTag)
    
    return matchesSearch && matchesTag
  })

  // Handle tag selection
  const handleTagChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedTag(e.target.value)
  }

  // Open chat with an agent
  const handleOpenChat = (agentId: string, e?: React.MouseEvent) => {
    // If the click was on a tag, prevent opening the chat
    if (e?.target instanceof HTMLElement && 
       (e.target.closest('.agent-tag') || e.target.closest('.agent-tag-wrapper'))) {
      return;
    }
    setSelectedAgent(agentId)
  }

  // Handle tag click
  const handleTagClick = (tag: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedTag(tag)
  }

  // Go back to agent list
  const handleBackToAgents = () => {
    setSelectedAgent(null)
  }

  // Reload agents
  const handleReload = () => {
    fetchAgents()
  }

  // If an agent is selected, show the chat interface
  if (selectedAgent) {
    return <AgentChat agentId={selectedAgent} onBack={handleBackToAgents} />
  }

  return (
    <div className="flex flex-col h-full p-6 bg-background overflow-auto">
      <div className="flex flex-col mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-semibold text-foreground">
            Agents <span className="text-xs bg-accent/20 text-muted-foreground px-1 rounded ml-1">BETA</span>
          </h1>
          <button 
            onClick={handleReload}
            disabled={isLoading}
            className="p-2 rounded-full hover:bg-accent/20 text-muted-foreground hover:text-foreground transition-colors"
            title="Refresh agents"
          >
            <RefreshCw size={18} className={isLoading ? "animate-spin" : ""} />
          </button>
        </div>
        <p className="text-muted-foreground text-sm">Supercharge your workflow with AI agents tailored to your exact needs</p>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <div className="relative">
            <select 
              className="bg-background border border-border rounded-md pl-3 pr-8 py-1 text-sm text-foreground appearance-none focus:outline-none focus:ring-1 focus:ring-primary [&>option]:!bg-[#1e1e2f] dark:[&>option]:!bg-[#1e1e2f] [&>option]:!text-foreground"
              value={selectedTag}
              onChange={handleTagChange}
            >
              <option value="">All tags</option>
              {allTags.map(tag => (
                <option key={tag} value={tag}>{tag}</option>
              ))}
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

      {isLoading ? (
        <div className="flex flex-col items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mb-4"></div>
          <p className="text-muted-foreground">Loading agents...</p>
        </div>
      ) : error ? (
        <div className="text-center py-10 rounded-lg border border-border bg-card p-6">
          <p className="text-red-500 mb-4">{error}</p>
          <button 
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            onClick={handleReload}
          >
            Try Again
          </button>
        </div>
      ) : filteredAgents.length === 0 ? (
        <div className="text-center py-10 rounded-lg border border-border bg-card p-6">
          <p className="text-muted-foreground mb-2">No agents found matching your filters</p>
          {filter || selectedTag ? (
            <button 
              className="text-primary hover:underline"
              onClick={() => { setFilter(''); setSelectedTag(''); }}
            >
              Clear filters
            </button>
          ) : (
            <p className="text-sm text-muted-foreground">
              Try refreshing or check your server connection
            </p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAgents.map(agent => (
            <div 
              key={agent.id} 
              className="bg-card border border-border rounded-lg overflow-hidden flex flex-col hover:border-primary hover:shadow-md hover:shadow-primary/10 transition-all cursor-pointer transform hover:-translate-y-1"
              onClick={(e) => handleOpenChat(agent.id, e)}
            >
              <div className="p-5">
                <div className="flex items-center space-x-4 mb-3">
                  <div className="flex-shrink-0">
                    <img 
                      src={getAgentIconPath(agent.id)} 
                      alt={agent.name} 
                      className="w-14 h-14 rounded-full object-cover border border-border shadow-sm"
                      loading="eager"
                      decoding="async"
                      onError={(e) => {
                        // If icon from local assets fails, try the URL from agent metadata
                        // Add size parameters for better resolution if it's an external URL
                        const iconUrl = agent.icon || '';
                        if (iconUrl.includes('placeholder.com')) {
                          // If already a placeholder URL, ensure high resolution
                          (e.target as HTMLImageElement).src = `https://via.placeholder.com/512x512?text=${encodeURIComponent(agent.name[0])}`;
                        } else if (iconUrl.startsWith('http')) {
                          // For other URLs, try to use as is with quality parameters if possible
                          const url = new URL(iconUrl);
                          if (url.hostname.includes('cloudinary')) {
                            // Add quality parameters for Cloudinary
                            (e.target as HTMLImageElement).src = `${iconUrl}/q_auto:best`;
                          } else {
                            (e.target as HTMLImageElement).src = iconUrl;
                          }
                        } else {
                          // Create high-res placeholder as last resort
                          (e.target as HTMLImageElement).src = `https://via.placeholder.com/512x512?text=${encodeURIComponent(agent.name[0])}&quality=100`;
                        }
                      }}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-foreground font-medium truncate text-lg">{agent.name}</p>
                    <div className="flex flex-wrap gap-1 mt-2 agent-tag-wrapper">
                      {agent.tags.map(tag => (
                        <span 
                          key={tag} 
                          className="agent-tag inline-flex items-center text-xs bg-accent/30 text-muted-foreground px-2 py-0.5 rounded cursor-pointer hover:bg-accent/50"
                          onClick={(e) => handleTagClick(tag, e)}
                        >
                          <Tag size={10} className="mr-1" /> {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">{agent.description}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Agents
