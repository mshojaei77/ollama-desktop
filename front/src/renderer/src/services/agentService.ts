import axios from 'axios';

// Define the base API URL
const API_URL = 'http://localhost:8000';

// Agent interfaces that match the backend structure
export interface Agent {
  id: string;
  name: string;
  description: string;
  icon: string;
  tags: string[];
}

export interface AgentListResponse {
  agents: Agent[];
  count: number;
}

export interface AgentMessageRequest {
  message: string;
  session_id?: string;
  context?: Record<string, any>;
}

export interface AgentMessageResponse {
  response: string;
  agent_id: string;
  session_id?: string;
}

// Agent service with methods to interact with the backend
const agentService = {
  // Get all available agents
  getAllAgents: async (): Promise<Agent[]> => {
    try {
      const response = await axios.get<AgentListResponse>(`${API_URL}/agents`);
      return response.data.agents;
    } catch (error) {
      console.error('Error fetching agents:', error);
      return [];
    }
  },

  // Get agents by tag
  getAgentsByTag: async (tag: string): Promise<Agent[]> => {
    try {
      const response = await axios.get<AgentListResponse>(`${API_URL}/agents/tag/${tag}`);
      return response.data.agents;
    } catch (error) {
      console.error(`Error fetching agents by tag ${tag}:`, error);
      return [];
    }
  },

  // Get a specific agent by ID
  getAgentById: async (agentId: string): Promise<Agent | null> => {
    try {
      const response = await axios.get<Agent>(`${API_URL}/agents/${agentId}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching agent ${agentId}:`, error);
      return null;
    }
  },

  // Send a message to an agent
  sendMessage: async (
    agentId: string,
    request: AgentMessageRequest
  ): Promise<AgentMessageResponse | null> => {
    try {
      const response = await axios.post<AgentMessageResponse>(
        `${API_URL}/agents/${agentId}/message`,
        request
      );
      return response.data;
    } catch (error) {
      console.error(`Error sending message to agent ${agentId}:`, error);
      return null;
    }
  },

  // Stream a message to an agent
  streamMessage: (agentId: string, request: AgentMessageRequest): EventSource => {
    // We need to post the message to the stream endpoint
    // However, native EventSource only supports GET requests
    // So we need to manually handle the POST request and SSE parsing
    
    // Create a custom EventSource-like object
    const customEventSource = new EventSource('data:text/event-stream;charset=utf-8,');
    
    // Store original event handlers
    const originalOnMessage = customEventSource.onmessage;
    const originalOnError = customEventSource.onerror;
    
    // Close the data: URL based EventSource immediately
    // We only use it to create a shell EventSource object
    customEventSource.close();
    
    // Make POST request using fetch
    fetch(`${API_URL}/agents/${agentId}/message/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    }).then(response => {
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }
      
      // Get the reader from the response body stream
      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      // Process the stream
      function processStream() {
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
  }
};

export default agentService; 