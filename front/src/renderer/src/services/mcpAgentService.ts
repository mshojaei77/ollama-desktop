import axios from 'axios';

// Define the base API URL
const API_URL = 'http://localhost:8000';

// Enhanced MCP Server Configuration interface
export interface MCPServerConfig {
  name: string;
  transport: 'stdio' | 'sse' | 'streamable-http';
  command?: string; // For stdio type
  url?: string; // For sse/streamable-http type
  args?: string[];
  env?: Record<string, string>;
  headers?: Record<string, string>;
  timeout?: number;
  sse_read_timeout?: number;
  enabled?: boolean;
  description?: string;
}

// Enhanced MCP Agent interfaces
export interface MCPAgent {
  id: string;
  name: string;
  description: string;
  instructions: string[];
  model_name: string;
  model_provider: string;
  mcp_servers: MCPServerConfig[];
  tags: string[];
  category?: string;
  icon: string;
  example_prompts: string[];
  welcome_message?: string;
  markdown: boolean;
  show_tool_calls: boolean;
  add_datetime_to_instructions: boolean;
  version: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface MCPAgentListResponse {
  agents: MCPAgent[];
  count: number;
  categories: string[];
  total_servers: number;
}

export interface CreateMCPAgentRequest {
  name: string;
  description?: string;
  instructions?: string[];
  model_name?: string;
  model_provider?: string;
  mcp_servers?: MCPServerConfig[];
  tags?: string[];
  category?: string;
  icon?: string;
  example_prompts?: string[];
  welcome_message?: string;
  markdown?: boolean;
  show_tool_calls?: boolean;
  add_datetime_to_instructions?: boolean;
}

export interface UpdateMCPAgentRequest {
  name?: string;
  description?: string;
  instructions?: string[];
  model_name?: string;
  model_provider?: string;
  mcp_servers?: MCPServerConfig[];
  tags?: string[];
  category?: string;
  icon?: string;
  example_prompts?: string[];
  welcome_message?: string;
  markdown?: boolean;
  show_tool_calls?: boolean;
  add_datetime_to_instructions?: boolean;
  is_active?: boolean;
}

export interface MCPAgentMessageRequest {
  message: string;
  session_id?: string;
  context?: Record<string, any>;
  stream?: boolean;
}

export interface MCPAgentMessageResponse {
  response: string;
  agent_id: string;
  session_id?: string;
  metadata?: Record<string, any>;
  tool_calls?: Array<Record<string, any>>;
}

export interface MCPServerTemplate {
  name: string;
  description: string;
  transport: string;
  command?: string;
  url?: string;
  env_vars: string[];
  category: string;
  tags: string[];
  example_instructions: string[];
  icon?: string;
}

export interface AgentStatus {
  agent_id: string;
  is_active: boolean;
  total_servers: number;
  active_servers: number;
  server_status: Array<{
    name: string;
    transport: string;
    enabled: boolean;
    description?: string;
  }>;
  model: string;
  category?: string;
  version: string;
}

export interface ValidationResult {
  valid: boolean;
  warnings: string[];
  errors: string[];
  server_validations: Array<{
    name: string;
    transport: string;
    valid: boolean;
    errors: string[];
    warnings: string[];
  }>;
}

// Enhanced MCP Agent service
const mcpAgentService = {
  // Get all MCP agents with enhanced filtering
  getAllAgents: async (params?: {
    category?: string;
    tag?: string;
    search?: string;
  }): Promise<MCPAgentListResponse> => {
    try {
      const queryParams = new URLSearchParams();
      if (params?.category) queryParams.append('category', params.category);
      if (params?.tag) queryParams.append('tag', params.tag);
      if (params?.search) queryParams.append('search', params.search);
      
      const url = `${API_URL}/mcp-agents/${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await axios.get<MCPAgentListResponse>(url);
      return response.data;
    } catch (error) {
      console.error('Error fetching MCP agents:', error);
      return { agents: [], count: 0, categories: [], total_servers: 0 };
    }
  },

  // Get agent categories
  getAgentCategories: async (): Promise<string[]> => {
    try {
      const response = await axios.get<{ categories: string[] }>(`${API_URL}/mcp-agents/categories`);
      return response.data.categories;
    } catch (error) {
      console.error('Error fetching agent categories:', error);
      return [];
    }
  },

  // Get MCP server templates
  getMCPServerTemplates: async (): Promise<MCPServerTemplate[]> => {
    try {
      const response = await axios.get<{ templates: MCPServerTemplate[] }>(`${API_URL}/mcp-agents/server-templates`);
      return response.data.templates;
    } catch (error) {
      console.error('Error fetching MCP server templates:', error);
      return [];
    }
  },

  // Get a specific MCP agent by ID
  getAgentById: async (agentId: string): Promise<MCPAgent | null> => {
    try {
      const response = await axios.get<MCPAgent>(`${API_URL}/mcp-agents/${agentId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching MCP agent ${agentId}:`, error);
      return null;
    }
  },

  // Get agent status
  getAgentStatus: async (agentId: string): Promise<AgentStatus | null> => {
    try {
      const response = await axios.get<AgentStatus>(`${API_URL}/mcp-agents/${agentId}/status`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching agent status ${agentId}:`, error);
      return null;
    }
  },

  // Validate agent configuration
  validateAgentConfig: async (agentId: string): Promise<ValidationResult | null> => {
    try {
      const response = await axios.get<ValidationResult>(`${API_URL}/mcp-agents/${agentId}/validate`);
      return response.data;
    } catch (error) {
      console.error(`Error validating agent config ${agentId}:`, error);
      return null;
    }
  },

  // Create a new MCP agent
  createAgent: async (request: CreateMCPAgentRequest): Promise<MCPAgent | null> => {
    try {
      const response = await axios.post<MCPAgent>(`${API_URL}/mcp-agents`, request);
      return response.data;
    } catch (error) {
      console.error('Error creating MCP agent:', error);
      throw error;
    }
  },

  // Update an existing MCP agent
  updateAgent: async (agentId: string, request: UpdateMCPAgentRequest): Promise<MCPAgent | null> => {
    try {
      const response = await axios.put<MCPAgent>(`${API_URL}/mcp-agents/${agentId}`, request);
      return response.data;
    } catch (error) {
      console.error(`Error updating MCP agent ${agentId}:`, error);
      throw error;
    }
  },

  // Delete an MCP agent (soft delete)
  deleteAgent: async (agentId: string): Promise<boolean> => {
    try {
      await axios.delete(`${API_URL}/mcp-agents/${agentId}`);
      return true;
    } catch (error) {
      console.error(`Error deleting MCP agent ${agentId}:`, error);
      return false;
    }
  },

  // Permanently delete an MCP agent
  deleteAgentPermanently: async (agentId: string): Promise<boolean> => {
    try {
      await axios.delete(`${API_URL}/mcp-agents/${agentId}/permanent`);
      return true;
    } catch (error) {
      console.error(`Error permanently deleting MCP agent ${agentId}:`, error);
      return false;
    }
  },

  // Start an MCP agent
  startAgent: async (agentId: string): Promise<boolean> => {
    try {
      const response = await axios.post(`${API_URL}/mcp-agents/${agentId}/start`);
      return response.status === 200;
    } catch (error) {
      console.error(`Error starting MCP agent ${agentId}:`, error);
      throw error;
    }
  },

  // Stop an MCP agent
  stopAgent: async (agentId: string): Promise<boolean> => {
    try {
      const response = await axios.post(`${API_URL}/mcp-agents/${agentId}/stop`);
      return response.status === 200;
    } catch (error) {
      console.error(`Error stopping MCP agent ${agentId}:`, error);
      throw error;
    }
  },

  // Send a message to an MCP agent
  sendMessage: async (
    agentId: string,
    request: MCPAgentMessageRequest
  ): Promise<MCPAgentMessageResponse | null> => {
    try {
      const response = await axios.post<MCPAgentMessageResponse>(
        `${API_URL}/mcp-agents/${agentId}/chat`,
        request
      );
      return response.data;
    } catch (error) {
      console.error(`Error sending message to MCP agent ${agentId}:`, error);
      return null;
    }
  },

  // Stream a message to an MCP agent with enhanced error handling
  streamMessage: (agentId: string, request: MCPAgentMessageRequest): EventSource => {
    // Create a custom EventSource-like object for POST requests
    const customEventSource = new EventSource('data:text/event-stream;charset=utf-8,');
    
    // Close the data: URL based EventSource immediately
    customEventSource.close();
    
    // Make POST request using fetch with enhanced error handling
    fetch(`${API_URL}/mcp-agents/${agentId}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
      body: JSON.stringify(request)
    }).then(response => {
      if (!response.ok) {
        throw new Error(`Server error: ${response.status} ${response.statusText}`);
      }
      
      if (!response.body) {
        throw new Error('Response body is null');
      }
      
      // Get the reader from the response body stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      // Process the stream
      function processStream(): void {
        reader.read().then(({ done, value }) => {
          if (done) {
            // End of stream
            if (customEventSource.onmessage) {
              const event = new MessageEvent('message', { 
                data: JSON.stringify({ done: true }) 
              });
              customEventSource.onmessage(event);
            }
            return;
          }
          
          // Decode the chunk and add to buffer
          buffer += decoder.decode(value, { stream: true });
          
          // Process complete SSE events in buffer
          const lines = buffer.split('\n\n');
          
          // Keep the last incomplete event (if any) in the buffer
          buffer = lines.pop() || '';
          
          // Process each complete event
          lines.forEach(line => {
            if (line.trim() && line.startsWith('data: ')) {
              const eventData = line.slice(6);
              
              // Dispatch the event
              if (customEventSource.onmessage) {
                const event = new MessageEvent('message', { data: eventData });
                customEventSource.onmessage(event);
              }
            }
          });
          
          // Continue reading
          processStream();
        }).catch(error => {
          console.error('Error reading stream:', error);
          if (customEventSource.onerror) {
            const event = new ErrorEvent('error', { 
              message: `Stream error: ${error.message}` 
            });
            customEventSource.onerror(event);
          }
        });
      }
      
      // Start processing the stream
      processStream();
      
    }).catch(error => {
      console.error('Error connecting to stream:', error);
      if (customEventSource.onerror) {
        const event = new ErrorEvent('error', { 
          message: `Connection error: ${error.message}` 
        });
        customEventSource.onerror(event);
      }
    });
    
    // Return the custom EventSource
    return customEventSource;
  },

  // Get available models
  getAvailableModels: async (): Promise<string[]> => {
    try {
      const response = await axios.get<{ models: string[] }>(`${API_URL}/mcp-agents/models/available`);
      return response.data.models;
    } catch (error) {
      console.error('Error fetching available models:', error);
      return [];
    }
  },

  // Cleanup all agents
  cleanupAllAgents: async (): Promise<boolean> => {
    try {
      await axios.post(`${API_URL}/mcp-agents/cleanup`);
      return true;
    } catch (error) {
      console.error('Error cleaning up MCP agents:', error);
      return false;
    }
  },

  // Utility function to create an agent from a template
  createAgentFromTemplate: (template: MCPServerTemplate, customizations?: Partial<CreateMCPAgentRequest>): CreateMCPAgentRequest => {
    const serverConfig: MCPServerConfig = {
      name: template.name.toLowerCase().replace(/\s+/g, '_'),
      transport: template.transport as 'stdio' | 'sse' | 'streamable-http',
      description: template.description,
      enabled: true,
    };

    if (template.command) {
      serverConfig.command = template.command;
    }
    if (template.url) {
      serverConfig.url = template.url;
    }
    if (template.env_vars.length > 0) {
      serverConfig.env = template.env_vars.reduce((acc, envVar) => {
        acc[envVar] = ''; // User will need to fill these in
        return acc;
      }, {} as Record<string, string>);
    }

    return {
      name: template.name + ' Agent',
      description: template.description,
      instructions: template.example_instructions.length > 0 
        ? template.example_instructions 
        : ['You are a helpful AI assistant.'],
      mcp_servers: [serverConfig],
      tags: template.tags,
      category: template.category,
      icon: template.icon || '🤖',
      example_prompts: [],
      welcome_message: `I'm your ${template.name} assistant! I can help you with ${template.description.toLowerCase()}.`,
      markdown: true,
      show_tool_calls: true,
      add_datetime_to_instructions: false,
      ...customizations,
    };
  },

  // Utility function to check if an agent needs configuration
  needsConfiguration: (agent: MCPAgent): boolean => {
    return agent.mcp_servers.some(server => {
      if (server.env) {
        return Object.values(server.env).some(value => !value);
      }
      return false;
    });
  },

  // Get configuration requirements for an agent
  getConfigurationRequirements: (agent: MCPAgent): string[] => {
    const requirements: string[] = [];
    
    agent.mcp_servers.forEach(server => {
      if (server.env) {
        Object.entries(server.env).forEach(([key, value]) => {
          if (!value) {
            requirements.push(`${server.name}: ${key}`);
          }
        });
      }
    });
    
    return requirements;
  },

  // Initialize pre-built agents (only if no agents exist)
  initializePrebuiltAgents: async (): Promise<{ prebuilt_created: boolean; message: string }> => {
    try {
      const response = await axios.post<{
        status: string;
        message: string;
        prebuilt_created: boolean;
      }>(`${API_URL}/mcp-agents/initialize-prebuilt`);
      return {
        prebuilt_created: response.data.prebuilt_created,
        message: response.data.message
      };
    } catch (error) {
      console.error('Error initializing pre-built agents:', error);
      return { prebuilt_created: false, message: 'Failed to initialize pre-built agents' };
    }
  },

  // Force create pre-built agents
  createPrebuiltAgents: async (): Promise<{ agents: MCPAgent[]; message: string }> => {
    try {
      const response = await axios.post<{
        status: string;
        message: string;
        agents: MCPAgent[];
      }>(`${API_URL}/mcp-agents/create-prebuilt`);
      return {
        agents: response.data.agents,
        message: response.data.message
      };
    } catch (error) {
      console.error('Error creating pre-built agents:', error);
      return { agents: [], message: 'Failed to create pre-built agents' };
    }
  },

  // Get pre-built agents
  getPrebuiltAgents: async (): Promise<MCPAgent[]> => {
    try {
      const response = await axios.get<{ agents: MCPAgent[]; count: number }>(`${API_URL}/mcp-agents/prebuilt`);
      return response.data.agents;
    } catch (error) {
      console.error('Error fetching pre-built agents:', error);
      return [];
    }
  },

  // Get user-created agents
  getUserCreatedAgents: async (): Promise<MCPAgent[]> => {
    try {
      const response = await axios.get<{ agents: MCPAgent[]; count: number }>(`${API_URL}/mcp-agents/user-created`);
      return response.data.agents;
    } catch (error) {
      console.error('Error fetching user-created agents:', error);
      return [];
    }
  }
};

export default mcpAgentService; 