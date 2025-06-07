import { useState, useEffect } from 'react'
import { Search, ChevronDown, Tag, RefreshCw, Plus, Settings, Bot, AlertTriangle, CheckCircle, Clock } from 'lucide-react'
import mcpAgentService, { MCPAgent, MCPAgentListResponse } from '../services/mcpAgentService'
import MCPAgentChat from '../components/MCPAgentChat'
import CreateMCPAgentModal from '../components/CreateMCPAgentModal'

function MCPAgents(): JSX.Element {
  const [filter, setFilter] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [selectedTag, setSelectedTag] = useState('')
  const [agents, setAgents] = useState<MCPAgent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [allCategories, setAllCategories] = useState<string[]>([])
  const [allTags, setAllTags] = useState<string[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [totalServers, setTotalServers] = useState(0)

  // Fetch agents from API with enhanced features
  const fetchAgents = async (options?: { category?: string; tag?: string; search?: string }) => {
    setIsLoading(true)
    setError(null)
    try {
      const response: MCPAgentListResponse = await mcpAgentService.getAllAgents(options)
      setAgents(response.agents)
      setAllCategories(response.categories)
      setTotalServers(response.total_servers)
      
      // Extract all unique tags from agents
      const tags = new Set<string>()
      response.agents.forEach(agent => {
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

  // Initialize sample agents if needed
  useEffect(() => {
    const initializeSamples = async () => {
      try {
        const result = await mcpAgentService.initializeSampleAgents()
        if (result.samples_created) {
          // Refresh the agents list if samples were created
          await fetchAgents()
        }
      } catch (error) {
        console.error('Error initializing sample agents:', error)
      }
    }

    // Only initialize samples after the initial fetch
    if (!isLoading && agents.length === 0) {
      initializeSamples()
    }
  }, [isLoading, agents.length])

  // Apply filters when they change
  useEffect(() => {
    const filterOptions: { category?: string; tag?: string; search?: string } = {}
    
    if (selectedCategory) filterOptions.category = selectedCategory
    if (selectedTag) filterOptions.tag = selectedTag
    if (filter.trim()) filterOptions.search = filter.trim()
    
    // Only refetch if we have filters
    if (Object.keys(filterOptions).length > 0) {
      fetchAgents(filterOptions)
    } else if (!selectedCategory && !selectedTag && !filter.trim()) {
      fetchAgents() // Fetch all agents when no filters
    }
  }, [selectedCategory, selectedTag, filter])

  // Handle category selection
  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCategory(e.target.value)
  }

  // Handle tag selection
  const handleTagChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedTag(e.target.value)
  }

  // Open chat with an agent
  const handleOpenChat = (agentId: string, e?: React.MouseEvent) => {
    // If the click was on a tag or status indicator, prevent opening the chat
    if (e?.target instanceof HTMLElement && 
       (e.target.closest('.agent-tag') || 
        e.target.closest('.agent-tag-wrapper') ||
        e.target.closest('.agent-status'))) {
      return;
    }
    setSelectedAgent(agentId)
  }

  // Handle tag click
  const handleTagClick = (tag: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedTag(tag)
  }

  // Handle category click
  const handleCategoryClick = (category: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedCategory(category)
  }

  // Go back to agent list
  const handleBackToAgents = () => {
    setSelectedAgent(null)
  }

  // Reload agents
  const handleReload = () => {
    fetchAgents()
  }

  // Handle agent creation
  const handleAgentCreated = () => {
    setShowCreateModal(false)
    fetchAgents() // Refresh the list
  }

  // Handle sample agents creation
  const handleCreateSamples = async () => {
    setIsLoading(true)
    try {
      const result = await mcpAgentService.createSampleAgents()
      if (result.agents.length > 0) {
        await fetchAgents() // Refresh the list
      }
    } catch (error) {
      console.error('Error creating sample agents:', error)
      setError('Failed to create sample agents')
    } finally {
      setIsLoading(false)
    }
  }

  // Clear all filters
  const clearFilters = () => {
    setFilter('')
    setSelectedCategory('')
    setSelectedTag('')
  }

  // Get agent status indicator
  const getAgentStatusIndicator = (agent: MCPAgent) => {
    const needsConfig = mcpAgentService.needsConfiguration(agent)
    const hasServers = agent.mcp_servers.length > 0
    
    if (needsConfig) {
      return (
        <div className="agent-status flex items-center gap-1 text-orange-500" title="Needs configuration">
          <AlertTriangle size={12} />
          <span className="text-xs">Config needed</span>
        </div>
      )
    } else if (hasServers) {
      return (
        <div className="agent-status flex items-center gap-1 text-green-500" title="Ready to use">
          <CheckCircle size={12} />
          <span className="text-xs">Ready</span>
        </div>
      )
    } else {
      return (
        <div className="agent-status flex items-center gap-1 text-gray-500" title="No MCP servers configured">
          <Clock size={12} />
          <span className="text-xs">Basic</span>
        </div>
      )
    }
  }

  // If an agent is selected, show the chat interface
  if (selectedAgent) {
    return <MCPAgentChat agentId={selectedAgent} onBack={handleBackToAgents} />
  }

  return (
    <div className="flex flex-col h-full p-6 bg-background overflow-auto">
      <div className="flex flex-col mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-semibold text-foreground flex items-center gap-3">
            <Bot className="w-8 h-8 text-primary" />
            MCP Agents
          </h1>
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              title="Create new MCP agent"
            >
              <Plus size={18} />
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
        <p className="text-muted-foreground text-sm">
          Build powerful AI agents with MCP (Model Context Protocol) integration. 
          Connect to external systems and create customized workflows.
          {totalServers > 0 && (
            <span className="ml-2 text-primary font-medium">
              {totalServers} total MCP servers configured
            </span>
          )}
        </p>
      </div>

      {/* Enhanced Filter Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div className="flex flex-wrap items-center gap-2">
          {/* Category Filter */}
          <div className="relative">
            <select 
              className="bg-background border border-border rounded-md pl-3 pr-8 py-1 text-sm text-foreground appearance-none focus:outline-none focus:ring-1 focus:ring-primary [&>option]:!bg-[#1e1e2f] dark:[&>option]:!bg-[#1e1e2f] [&>option]:!text-foreground"
              value={selectedCategory}
              onChange={handleCategoryChange}
            >
              <option value="">All categories</option>
              {allCategories.map(category => (
                <option key={category} value={category}>
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-muted-foreground">
              <ChevronDown className="h-4 w-4" />
            </div>
          </div>

          {/* Tag Filter */}
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

          {/* Clear Filters Button */}
          {(selectedCategory || selectedTag || filter) && (
            <button 
              onClick={clearFilters}
              className="text-xs text-muted-foreground hover:text-foreground px-2 py-1 rounded hover:bg-accent/20 transition-colors"
            >
              Clear filters
            </button>
          )}
        </div>
        
        {/* Search */}
        <div className="flex items-center space-x-2">
          <div className="relative">
            <input
              type="text"
              placeholder="Search agents..."
              className="bg-background border border-border rounded-md pl-8 pr-3 py-1 text-sm w-64"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
            <Search className="h-4 w-4 text-muted-foreground absolute left-2 top-1/2 transform -translate-y-1/2" />
          </div>
        </div>
      </div>

      {/* Results Summary */}
      {!isLoading && (
        <div className="flex items-center justify-between text-sm text-muted-foreground mb-4">
          <span>
            {agents.length} agent{agents.length !== 1 ? 's' : ''} found
            {(selectedCategory || selectedTag || filter) && (
              <span className="ml-1">
                {selectedCategory && ` in ${selectedCategory}`}
                {selectedTag && ` tagged with ${selectedTag}`}
                {filter && ` matching "${filter}"`}
              </span>
            )}
          </span>
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mb-4"></div>
          <p className="text-muted-foreground">Loading MCP agents...</p>
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
      ) : agents.length === 0 ? (
        <div className="text-center py-10 rounded-lg border border-border bg-card p-6">
          {(selectedCategory || selectedTag || filter) ? (
            <>
              <Bot className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">No Matching Agents</h3>
              <p className="text-muted-foreground mb-4">
                No agents found matching your current filters.
              </p>
              <button 
                className="text-primary hover:underline"
                onClick={clearFilters}
              >
                Clear filters to see all agents
              </button>
            </>
          ) : (
            <>
              <Bot className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">No MCP Agents Yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first MCP agent to get started with Model Context Protocol integration.
              </p>
              <div className="flex flex-col sm:flex-row gap-2 justify-center">
                <button 
                  onClick={() => setShowCreateModal(true)}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                >
                  Create Your First Agent
                </button>
                <button 
                  onClick={handleCreateSamples}
                  disabled={isLoading}
                  className="px-4 py-2 bg-accent text-accent-foreground rounded-md hover:bg-accent/90 transition-colors disabled:opacity-50"
                >
                  {isLoading ? 'Creating...' : 'Create Sample Agents'}
                </button>
              </div>
            </>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map(agent => (
            <div 
              key={agent.id} 
              className="bg-card border border-border rounded-lg overflow-hidden flex flex-col hover:border-primary hover:shadow-md hover:shadow-primary/10 transition-all cursor-pointer transform hover:-translate-y-1"
              onClick={(e) => handleOpenChat(agent.id, e)}
            >
              <div className="p-5">
                <div className="flex items-start space-x-4 mb-3">
                  <div className="flex-shrink-0">
                    {agent.icon ? (
                      <div className="w-14 h-14 rounded-full bg-primary/10 border border-border shadow-sm flex items-center justify-center text-2xl">
                        {agent.icon}
                      </div>
                    ) : (
                      <div className="w-14 h-14 rounded-full bg-primary/10 border border-border shadow-sm flex items-center justify-center">
                        <Bot className="w-8 h-8 text-primary" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <p className="text-foreground font-medium truncate text-lg">{agent.name}</p>
                      {getAgentStatusIndicator(agent)}
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">{agent.model_provider}/{agent.model_name}</p>
                    
                    {/* Category and Tags */}
                    <div className="flex flex-wrap gap-1 agent-tag-wrapper">
                      {agent.category && (
                        <span 
                          className="inline-flex items-center text-xs bg-primary/20 text-primary px-2 py-0.5 rounded cursor-pointer hover:bg-primary/30"
                          onClick={(e) => handleCategoryClick(agent.category!, e)}
                          title={`Category: ${agent.category}`}
                        >
                          {agent.category}
                        </span>
                      )}
                      {agent.tags.slice(0, 2).map(tag => (
                        <span 
                          key={tag} 
                          className="agent-tag inline-flex items-center text-xs bg-accent/30 text-muted-foreground px-2 py-0.5 rounded cursor-pointer hover:bg-accent/50"
                          onClick={(e) => handleTagClick(tag, e)}
                          title={`Filter by tag: ${tag}`}
                        >
                          <Tag size={10} className="mr-1" /> {tag}
                        </span>
                      ))}
                      {agent.tags.length > 2 && (
                        <span className="text-xs text-muted-foreground px-2 py-0.5">
                          +{agent.tags.length - 2} more
                        </span>
                      )}
                      {agent.mcp_servers.length > 0 && (
                        <span className="inline-flex items-center text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">
                          {agent.mcp_servers.length} MCP Server{agent.mcp_servers.length > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground line-clamp-2">{agent.description}</p>
                
                {/* Configuration Warning */}
                {mcpAgentService.needsConfiguration(agent) && (
                  <div className="mt-2 p-2 bg-orange-500/10 border border-orange-500/20 rounded text-xs text-orange-400">
                    <AlertTriangle size={12} className="inline mr-1" />
                    Requires configuration: {mcpAgentService.getConfigurationRequirements(agent).join(', ')}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Agent Modal */}
      {showCreateModal && (
        <CreateMCPAgentModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={handleAgentCreated}
        />
      )}
    </div>
  )
}

export default MCPAgents 