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
  AvailableChatsResponse
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
const fetchModels = async (): Promise<string[]> => {
  try {
    const { data } = await apiClient.get<ModelsResponse>('/models')
    return data.models
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

        const reader = response.body!.getReader()
        const decoder = new TextDecoder()

        function processStream(): Promise<string> {
          return reader.read().then(({ done, value }) => {
            if (done) {
              return fullResponse
            }

            const chunk = decoder.decode(value)

            const lines = chunk.split('\n\n')

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const jsonStr = line.slice(6) // Remove 'data: ' prefix
                  const data = JSON.parse(jsonStr)

                  if (data.text) {
                    fullResponse += data.text
                    onChunk(data.text)
                  }

                  if (data.done) {
                    reader.cancel()
                    return fullResponse
                  }

                  if (data.error) {
                    reader.cancel()
                    throw new Error(data.error)
                  }
                } catch {
                  // Ignore invalid JSON, might be partial chunks
                }
              }
            }

            return processStream()
          })
        }

        return processStream()
      })
      .then((result) => resolve(result))
      .catch((error) => {
        console.error('Fetch streaming error:', error)
        reject(error)
      })
  })
}

const sendMessage = async (
  params: SendMessageParams,
  onStreamUpdate?: (chunk: string) => void
): Promise<SendMessageResponse> => {
  try {
    const url = `${apiClient.defaults.baseURL}/chat/message/stream`

    const response = await createFetchStream(
      url,
      {
        message: params.message,
        session_id: params.session_id
      },
      (chunk) => {
        if (onStreamUpdate) {
          onStreamUpdate(chunk)
        }
      }
    )

    return { response }
  } catch (error) {
    console.error('Error sending message:', error)
    throw new Error('Failed to send message. Please try again.')
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
export const useModels = (enabled: boolean = true): UseQueryResult<string[], Error> => {
  return useQuery({
    queryKey: ['models'],
    queryFn: fetchModels,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
    enabled
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
      const userMessageId = Date.now().toString()

      const userMessage = {
        id: userMessageId,
        role: 'user' as const,
        content: variables.message,
        timestamp: new Date()
      }

      // Add user message to store
      addMessage(userMessage)

      const assistantMessageId = (Date.now() + 1).toString()
      const assistantMessage = {
        id: assistantMessageId,
        role: 'assistant' as const,
        content: '', // Start with empty content that will be updated during streaming
        timestamp: new Date()
      }

      addMessage(assistantMessage)

      try {
        // Only one API call that handles both streaming updates and returns the final response
        return await sendMessage(variables, (chunk) => {
          // Update message in the UI as chunks come in
          updateMessage(assistantMessageId, (content) => content + chunk)
        })
      } catch (error) {
        // Handle any errors during streaming
        console.error('Streaming error:', error)
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
