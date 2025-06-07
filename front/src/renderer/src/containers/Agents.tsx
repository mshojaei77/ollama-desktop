import { useState, useEffect } from 'react'
import { Search, ChevronDown, Tag, RefreshCw, Plus, MoreVertical, Trash2 } from 'lucide-react'
import AgentChat from '../components/AgentChat'
import { getAgentIconPath } from '../utils'
import mcpAgentService, { MCPAgent } from '../services/mcpAgentService'
import DeleteMCPAgentModal from '../components/DeleteMCPAgentModal'

function Agents(): JSX.Element {
  const [filter, setFilter] = useState('')
  const [selectedTag, setSelectedTag] = useState('')
  const [agents, setAgents] = useState<MCPAgent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [allTags, setAllTags] = useState<string[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [showCreateAgent, setShowCreateAgent] = useState(false)
  const [agentToDelete, setAgentToDelete] = useState<MCPAgent | null>(null)
  const [showDropdownFor, setShowDropdownFor] = useState<string | null>(null)

  // Fetch MCP agents from API
  const fetchAgents = async () => {
    setIsLoading(true)
    setError(null)
    try {
      // Service returns a response object { agents, count, ... } or directly an array
      const data = await mcpAgentService.getAllAgents()
      const agentList = Array.isArray(data) ? data : data.agents
      setAgents(agentList)
      
      // Extract all unique tags from agents
      const tags = new Set<string>()
      agentList.forEach(agent => {
        agent.tags.forEach(tag => tags.add(tag))
      })
      setAllTags(Array.from(tags).sort())
    } catch (err) {
      console.error('Failed to fetch MCP agents:', err)
      setError('Failed to load MCP agents. Please try again.')
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
  const handleOpenChat = async (agentId: string, e?: React.MouseEvent) => {
    // If the click was on a tag or dropdown, prevent opening the chat
    if (e?.target instanceof HTMLElement && 
       (e.target.closest('.agent-tag') || 
        e.target.closest('.agent-tag-wrapper') ||
        e.target.closest('.agent-dropdown'))) {
      return;
    }
    
    try {
      // Start the MCP agent if it's not already active
      await mcpAgentService.startAgent(agentId)
      setSelectedAgent(agentId)
    } catch (err) {
      console.error('Failed to start MCP agent:', err)
      setError('Failed to start agent. Please try again.')
    }
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

  // Handle delete confirmation
  const handleDeleteAgent = async (agentId: string, permanent: boolean) => {
    try {
      // Always use permanent delete since we removed soft delete option
      await mcpAgentService.deleteAgentPermanently(agentId)
      
      // Refresh the agents list
      await fetchAgents()
    } catch (error) {
      console.error('Error deleting agent:', error)
      throw error // Re-throw to be handled by the modal
    }
  }

  // Toggle dropdown menu
  const handleDropdownToggle = (agentId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setShowDropdownFor(showDropdownFor === agentId ? null : agentId)
  }

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setShowDropdownFor(null)
    }
    
    if (showDropdownFor) {
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [showDropdownFor])

  // If an agent is selected, show the chat interface
  if (selectedAgent) {
    return <AgentChat agentId={selectedAgent} onBack={handleBackToAgents} isMCPAgent={true} />
  }

  return (
    <div className="flex flex-col h-full p-6 bg-background overflow-auto">
      <div className="flex flex-col mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-semibold text-foreground">
            MCP Agents <span className="text-xs bg-accent/20 text-muted-foreground px-1 rounded ml-1">BETA</span>
          </h1>
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setShowCreateAgent(true)}
              className="px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors flex items-center gap-2"
              title="Create new MCP agent"
            >
              <Plus size={16} />
              Create Agent
            </button>
            <button 
              onClick={handleReload}
              disabled={isLoading}
              className="p-2 rounded-full hover:bg-accent/20 text-muted-foreground hover:text-foreground transition-colors"
              title="Refresh agents"
            >
              <RefreshCw size={18} className={isLoading ? "animate-spin" : ""} />
            </button>
          </div>
        </div>
        <p className="text-muted-foreground text-sm">Build powerful AI agents with MCP (Model Context Protocol) integration for external tools and services</p>
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
          <p className="text-muted-foreground mb-2">No MCP agents found matching your filters</p>
          {filter || selectedTag ? (
            <button 
              className="text-primary hover:underline"
              onClick={() => { setFilter(''); setSelectedTag(''); }}
            >
              Clear filters
            </button>
          ) : (
            <div>
              <p className="text-sm text-muted-foreground mb-4">
                No MCP agents available. Create your first agent to get started.
              </p>
              <button 
                onClick={() => setShowCreateAgent(true)}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                Create First Agent
              </button>
            </div>
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
                        // MCP agents don't have icons by default, so create a placeholder
                        (e.target as HTMLImageElement).src = `https://via.placeholder.com/512x512?text=${encodeURIComponent(agent.name[0])}&quality=100`;
                      }}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <p className="text-foreground font-medium truncate text-lg">{agent.name}</p>
                      
                      {/* Dropdown Menu */}
                      <div className="agent-dropdown relative">
                        <button
                          onClick={(e) => handleDropdownToggle(agent.id, e)}
                          className="p-1 rounded hover:bg-[hsl(var(--accent))]/30 text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors"
                          title="More options"
                        >
                          <MoreVertical size={16} />
                        </button>
                        
                        {showDropdownFor === agent.id && (
                          <div className="absolute right-0 top-8 bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-md shadow-lg z-20 min-w-[150px] py-1">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                setAgentToDelete(agent)
                                setShowDropdownFor(null)
                              }}
                              className="w-full flex items-center gap-2 px-3 py-2 text-left text-sm text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-colors rounded-sm"
                            >
                              <Trash2 size={14} />
                              Delete Agent
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                    
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

      {/* Delete Agent Modal */}
      {agentToDelete && (
        <DeleteMCPAgentModal
          agent={agentToDelete}
          onClose={() => setAgentToDelete(null)}
          onDelete={handleDeleteAgent}
        />
      )}
    </div>
  )
}

export default Agents
