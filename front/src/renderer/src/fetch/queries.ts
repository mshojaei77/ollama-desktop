import {
  useMutation,
  useQuery,
  QueryClient,
  UseQueryResult,
  UseMutationResult
} from '@tanstack/react-query'
import apiClient from './api-client'
import {
  InitializeChatParams,
  InitializeChatResponse,
  SendMessageParams,
  SendMessageResponse,
  ModelsResponse,
  ChatHistoryResponse,
  AvailableChatsResponse,
  MCPServersResponse,
  ModelInfo,
  ModelDetails
} from './types'
import { useChatStore } from '../store/chatStore'

// Create Query Client
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
})

// API functions
const fetchModels = async (): Promise<ModelsResponse> => {
  try {
    const { data } = await apiClient.get<ModelsResponse>('/models')
    // No need to normalize anymore, just return the data
    // Ensure the response conforms to the expected structure
    if (!data || !Array.isArray(data.models)) {
      console.error('Invalid models response format:', data)
      throw new Error('Invalid response format received from API.')
    }
    // Optionally, validate each model object has a name
    data.models.forEach((model, index) => {
      if (!model || typeof model.name !== 'string') {
        console.warn(`Model at index ${index} has invalid format:`, model);
        // Depending on strictness, you might want to filter these out or throw an error
      }
    });
    return data
  } catch (error) {
    console.error('Error fetching models:', error)
    throw new Error('Failed to fetch models. Is the API server running?')
  }
}

const initializeChat = async (params: InitializeChatParams): Promise<InitializeChatResponse> => {
  try {
    const { data } = await apiClient.post<InitializeChatResponse>('/chat/initialize', params)
    return data
  } catch (error) {
    console.error('Error initializing chat:', error)
    throw new Error('Failed to initialize chat. Please try again.')
  }
}

const createFetchStream = (
  url: string,
  body: object,
  onChunk: (chunk: string) => void
): Promise<string> => {
  return new Promise((resolve, reject) => {
    let fullResponse = ''
    let errorMessage = ''

    console.log('Initiating streaming request to:', url, 'with body:', body)

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`)
        }
        console.log('Stream connection established, status:', response.status)
        
        const reader = response.body!.getReader()
        const decoder = new TextDecoder()

        function processStream(): Promise<string> {
          return reader.read().then(({ done, value }) => {
            if (done) {
              console.log('Stream completed, full response length:', fullResponse.length)
              return fullResponse
            }

            const chunk = decoder.decode(value)
            console.log('Received chunk:', chunk)

            const lines = chunk.split('\n\n')
            let processedAny = false

            for (const line of lines) {
              if (line.trim() === '') continue;
              
              if (line.startsWith('data: ')) {
                try {
                  const jsonStr = line.slice(6).trim() // Remove 'data: ' prefix
                  console.log('Processing JSON data:', jsonStr)
                  
                  if (!jsonStr) {
                    console.warn('Empty JSON string in data line')
                    continue
                  }
                  
                  const data = JSON.parse(jsonStr)
                  console.log('Parsed response data:', data)

                  if (data.text) {
                    console.log('Received text chunk:', data.text)
                    fullResponse += data.text
                    onChunk(data.text)
                    processedAny = true
                  } else if (data.response) {
                    // Some APIs might use 'response' instead of 'text'
                    console.log('Received response chunk:', data.response)
                    fullResponse += data.response
                    onChunk(data.response)
                    processedAny = true
                  }

                  if (data.done) {
                    console.log('Stream marked as done by server')
                    reader.cancel()
                    return fullResponse
                  }

                  if (data.error) {
                    errorMessage = data.error
                    console.error('Error in stream data:', errorMessage)
                    reader.cancel()
                    throw new Error(data.error)
                  }
                } catch (error) {
                  // Log the error but don't reject - could be partial chunks
                  console.warn('Error parsing JSON from stream:', error, 'for line:', line)
                }
              } else {
                console.log('Non-data line received:', line)
              }
            }

            if (!processedAny) {
              console.warn('No data processed from chunk')
            }

            return processStream()
          })
        }

        return processStream()
      })
      .then((result) => {
        console.log('Stream complete, resolving with result length:', result.length)
        resolve(result)
      })
      .catch((error) => {
        console.error('Fetch streaming error:', error)
        if (errorMessage) {
          reject(new Error(errorMessage))
        } else {
          reject(error)
        }
      })
  })
}

const sendMessage = async (
  params: SendMessageParams,
  onStreamUpdate?: (chunk: string) => void
): Promise<SendMessageResponse> => {
  try {
    const url = `${apiClient.defaults.baseURL}/chat/message/stream`
    console.log('Sending message to stream endpoint:', params.message.substring(0, 20) + '...')

    // Track if we've received any valid text chunks
    let hasReceivedValidData = false;
    
    const response = await createFetchStream(
      url,
      {
        message: params.message,
        session_id: params.session_id
      },
      (chunk) => {
        if (chunk && chunk.trim()) {
          hasReceivedValidData = true;
          if (onStreamUpdate) {
            console.log('Calling stream update with chunk length:', chunk.length)
            onStreamUpdate(chunk)
          }
        } else {
          console.warn('Received empty chunk from API')
        }
      }
    )

    console.log('Stream finished, full response length:', response.length)
    
    // If we never received valid data but the API didn't error, send a fallback message
    if (!hasReceivedValidData && response.trim() === '') {
      console.warn('No valid data received from API during streaming, using fallback message')
      const fallbackMessage = "I'm sorry, I couldn't generate a response. Please try again.";
      
      if (onStreamUpdate) {
        onStreamUpdate(fallbackMessage);
      }
      
      return { response: fallbackMessage };
    }
    
    return { response }
  } catch (error) {
    console.error('Error sending message:', error)
    throw error instanceof Error ? error : new Error('Failed to send message. Please try again.')
  }
}

const fetchChatHistory = async (sessionId: string): Promise<ChatHistoryResponse> => {
  try {
    const { data } = await apiClient.get<ChatHistoryResponse>(`/chat/history/${sessionId}`)

    // Additional log to help debug the actual response structure
    console.log('Raw chat history data:', data)

    return data
  } catch (error) {
    console.error('Error fetching chat history:', error)
    throw new Error('Failed to fetch chat history. Please try again.')
  }
}

const fetchAvailableChats = async (
  includeInactive = false,
  limit = 100,
  offset = 0
): Promise<AvailableChatsResponse> => {
  try {
    const { data } = await apiClient.get<AvailableChatsResponse>('/chats', {
      params: { include_inactive: includeInactive, limit, offset }
    })
    return data
  } catch (error) {
    console.error('Error fetching available chats:', error)
    throw new Error('Failed to fetch available chats. Please try again.')
  }
}

const searchChats = async (
  query: string,
  includeInactive = false,
  limit = 100,
  offset = 0
): Promise<AvailableChatsResponse> => {
  try {
    const { data } = await apiClient.get<AvailableChatsResponse>('/chats/search', {
      params: { q: query, include_inactive: includeInactive, limit, offset }
    })
    return data
  } catch (error) {
    console.error('Error searching chats:', error)
    throw new Error('Failed to search chats. Please try again.')
  }
}

// Check API connection
export const checkApiConnection = async (): Promise<boolean> => {
  try {
    await apiClient.get('/')
    return true
  } catch (error) {
    console.error('API connection error:', error)
    return false
  }
}

// React Query hooks
export const useModels = (enabled: boolean = true): UseQueryResult<ModelsResponse, Error> => {
  return useQuery<ModelsResponse, Error>({
    queryKey: ['models'],
    queryFn: fetchModels,
    enabled: enabled
  })
}

export const useInitializeChat = (): UseMutationResult<
  InitializeChatResponse,
  Error,
  InitializeChatParams
> => {
  // Access Zustand store
  const setSessionId = useChatStore((state) => state.setSessionId)
  const setModelName = useChatStore((state) => state.setModelName)
  const setSessionActive = useChatStore((state) => state.setSessionActive)
  const clearMessages = useChatStore((state) => state.clearMessages)

  return useMutation({
    mutationFn: initializeChat,
    onSuccess: (data) => {
      // Update Zustand store with session data
      setSessionId(data.session_id)
      setModelName(data.model_name)
      setSessionActive(true)
      clearMessages()
    },
    onError: () => {
      // Reset store on error
      setSessionId(null)
      setModelName('')
      setSessionActive(false)
    }
  })
}

export const useSendMessage = (): UseMutationResult<
  SendMessageResponse,
  Error,
  SendMessageParams
> => {
  // Access Zustand store for adding messages
  const addMessage = useChatStore((state) => state.addMessage)
  const updateMessage = useChatStore((state) => state.updateMessage)

  return useMutation({
    mutationFn: async (variables: SendMessageParams) => {
      console.log('Starting message mutation for session:', variables.session_id)
      const userMessageId = Date.now().toString()

      const userMessage = {
        id: userMessageId,
        role: 'user' as const,
        content: variables.message,
        timestamp: new Date()
      }

      // Add user message to store
      console.log('Adding user message to store')
      addMessage(userMessage)

      const assistantMessageId = (Date.now() + 1).toString()
      const assistantMessage = {
        id: assistantMessageId,
        role: 'assistant' as const,
        content: '', // Start with empty content that will be updated during streaming
        timestamp: new Date()
      }

      console.log('Adding assistant message placeholder with ID:', assistantMessageId)
      addMessage(assistantMessage)

      try {
        // Only one API call that handles both streaming updates and returns the final response
        console.log('Starting stream for message')
        const result = await sendMessage(variables, (chunk) => {
          // Update message in the UI as chunks come in
          console.log('Received chunk in mutation handler:', chunk?.length)
          updateMessage(assistantMessageId, (prevContent) => {
            const newContent = prevContent + chunk;
            console.log('Updating message content, new length:', newContent.length)
            return newContent
          })
        })
        
        console.log('Message stream completed successfully')
        return result
      } catch (error) {
        // Handle any errors during streaming
        console.error('Streaming error in mutation:', error)
        updateMessage(
          assistantMessageId,
          (content) =>
            content + `\n\nError: ${error instanceof Error ? error.message : String(error)}`
        )
        throw error // Re-throw to let React Query handle the error state
      }
    }
  })
}

export const useChatHistory = (
  sessionId: string | null
): UseQueryResult<ChatHistoryResponse, Error> => {
  return useQuery({
    queryKey: ['chatHistory', sessionId],
    queryFn: () => {
      if (!sessionId) {
        throw new Error('Session ID is required to fetch chat history')
      }
      return fetchChatHistory(sessionId)
    },
    enabled: !!sessionId, // Only run the query if sessionId exists
    refetchOnWindowFocus: true
  })
}

export const useAvailableChats = (
  includeInactive: boolean,
  limit: number,
  offset: number
): UseQueryResult<AvailableChatsResponse, Error> => {
  return useQuery({
    queryKey: ['availableChats', includeInactive, limit, offset],
    queryFn: () => fetchAvailableChats(includeInactive, limit, offset),
    enabled: true
  })
}

export const useSearchChats = (
  query: string,
  includeInactive: boolean,
  limit: number,
  offset: number
): UseQueryResult<AvailableChatsResponse, Error> => {
  return useQuery({
    queryKey: ['searchChats', query, includeInactive, limit, offset],
    queryFn: () => searchChats(query, includeInactive, limit, offset),
    enabled: !!query && query.trim().length > 0
  })
}

const fetchMCPServers = async (): Promise<MCPServersResponse> => {
  try {
    const { data } = await apiClient.get<MCPServersResponse>('/mcp/servers')
    return data
  } catch (error) {
    console.error('Error fetching MCP servers:', error)
    throw new Error('Failed to fetch MCP servers. Please try again.')
  }
}

export const useMCPServers = (): UseQueryResult<MCPServersResponse, Error> => {
  return useQuery({
    queryKey: ['mcpServers'],
    queryFn: fetchMCPServers
  })
}

const fetchModelInfo = async (modelName: string): Promise<ModelDetails> => {
  // Make sure modelName is properly encoded for the URL
  const encodedModelName = encodeURIComponent(modelName);
  try {
    const { data } = await apiClient.get<ModelDetails>(`/models/${encodedModelName}/info`)
    return data
  } catch (error) {
    console.error(`Error fetching model info for ${modelName}:`, error)
    throw new Error(`Failed to fetch info for model ${modelName}. Please try again.`)
  }
}

// Hook to fetch detailed info for a specific model
export const useModelInfo = (modelName: string | null): UseQueryResult<ModelDetails, Error> => {
  return useQuery<ModelDetails, Error>({
    queryKey: ['modelInfo', modelName],
    queryFn: () => {
      if (!modelName) {
        // Should not happen if enabled is false, but good practice
        throw new Error('Model name is required to fetch info.')
      }
      return fetchModelInfo(modelName)
    },
    enabled: !!modelName, // Only run the query if modelName is provided
    staleTime: 5 * 60 * 1000 // Cache for 5 minutes
  })
}
