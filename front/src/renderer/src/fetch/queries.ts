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

const sendMessage = async (params: SendMessageParams): Promise<SendMessageResponse> => {
  try {
    const { data } = await apiClient.post<SendMessageResponse>('/chat/message', params)
    return data
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

  return useMutation({
    mutationFn: sendMessage,
    onMutate: (variables) => {
      // Create a new user message for optimistic update
      const userMessage = {
        id: Date.now().toString(),
        role: 'user' as const,
        content: variables.message,
        timestamp: new Date()
      }

      // Add user message to store
      addMessage(userMessage)
    },
    onSuccess: (data) => {
      // Add assistant response to store
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: data.response,
        timestamp: new Date()
      }

      addMessage(assistantMessage)
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
