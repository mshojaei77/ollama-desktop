import { useState, useEffect, useRef } from 'react'
import { Input } from '@renderer/components/ui/input'
import { Button } from '@renderer/components/ui/button'
import axios from 'axios'
import { useQuery, useMutation, QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Create API client
const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Create Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
})

// API functions
const api = {
  getModels: async () => {
    try {
      const { data } = await apiClient.get('/models')
      return data.models
    } catch (error) {
      console.error('Error fetching models:', error)
      throw new Error('Failed to fetch models. Is the API server running?')
    }
  },
  initializeChat: async (params: { model_name: string; system_message?: string }) => {
    try {
      const { data } = await apiClient.post('/chat/initialize', params)
      return data
    } catch (error) {
      console.error('Error initializing chat:', error)
      throw new Error('Failed to initialize chat. Please try again.')
    }
  },
  sendMessage: async (params: { message: string; session_id: string }) => {
    try {
      const { data } = await apiClient.post('/chat/message', params)
      return data
    } catch (error) {
      console.error('Error sending message:', error)
      throw new Error('Failed to send message. Please try again.')
    }
  }
}

// Wrap the component with QueryClientProvider
function ChatApp(): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <Chat />
    </QueryClientProvider>
  )
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatSession {
  id: string
  model: string
}

function Chat(): JSX.Element {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [session, setSession] = useState<ChatSession | null>(null)
  const [selectedModel, setSelectedModel] = useState('llama3.2')
  const [apiConnected, setApiConnected] = useState<boolean | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Check API connection
  useEffect(() => {
    const checkApiConnection = async () => {
      try {
        await apiClient.get('/')
        setApiConnected(true)
      } catch (error) {
        console.error('API connection error:', error)
        setApiConnected(false)
      }
    }

    checkApiConnection()
  }, [])

  // Fetch models using React Query
  const {
    data: models = [],
    isLoading: isLoadingModels,
    error: modelsError
  } = useQuery({
    queryKey: ['models'],
    queryFn: api.getModels,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
    enabled: apiConnected === true
  })

  // Initialize chat mutation
  const { mutate: initializeChat, isPending: isInitializing } = useMutation({
    mutationFn: api.initializeChat,
    onSuccess: (data) => {
      setSession({
        id: data.session_id,
        model: data.model
      })

      // Add welcome message
      setMessages([
        {
          id: Date.now().toString(),
          role: 'assistant',
          content: `Hello! I'm running on the ${data.model} model. How can I help you today?`,
          timestamp: new Date()
        }
      ])
    },
    onError: (error) => {
      console.error('Failed to initialize chat:', error)
      // Show error in UI
      alert(
        `Failed to initialize chat: ${error instanceof Error ? error.message : 'Unknown error'}`
      )
    }
  })

  // Send message mutation
  const { mutate: sendMessageMutation, isPending: isSending } = useMutation({
    mutationFn: api.sendMessage,
    onSuccess: (data) => {
      // Add assistant response to chat
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response,
          timestamp: new Date()
        }
      ])
    },
    onError: (error) => {
      console.error('Failed to send message:', error)
      // Add error message
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
          timestamp: new Date()
        }
      ])
    }
  })

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Handler to start a new chat
  const handleInitializeChat = () => {
    initializeChat({
      model_name: selectedModel,
      system_message: 'You are a helpful assistant.'
    })
  }

  // Send message handler
  const sendMessage = () => {
    if (!input.trim() || !session) return

    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')

    // Call the mutation
    sendMessageMutation({
      message: input,
      session_id: session.id
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Render API connection error
  if (apiConnected === false) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6">
        <div className="text-center max-w-md">
          <h1 className="mb-4 text-2xl font-bold text-red-500">API Connection Error</h1>
          <p className="mb-6">
            Could not connect to the Ollama API server at <code>http://localhost:8000</code>.
          </p>
          <p className="mb-6">Please make sure the API server is running and try again.</p>
          <Button onClick={() => window.location.reload()}>Retry Connection</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full max-h-screen bg-[hsl(var(--background))]">
      {!session ? (
        <div className="flex flex-col items-center justify-center h-full gap-6 p-6">
          <div className="text-center">
            <h1 className="mb-4 text-2xl font-bold">Welcome to Ollama Chat</h1>
            <p className="mb-6 text-[hsl(var(--muted-foreground))]">
              Select a model to start chatting
            </p>
          </div>

          <div className="w-full max-w-md space-y-4">
            {modelsError ? (
              <div className="p-3 mb-4 border rounded border-red-300 bg-red-50 text-red-700">
                <p className="font-medium">Error loading models</p>
                <p className="text-sm">
                  {modelsError instanceof Error ? modelsError.message : 'Please try again later.'}
                </p>
              </div>
            ) : null}

            <select
              className="w-full p-2 border rounded-md bg-[hsl(var(--background))] border-[hsl(var(--input))]"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={isLoadingModels || apiConnected !== true}
            >
              {isLoadingModels ? (
                <option>Loading models...</option>
              ) : models.length === 0 ? (
                <option>No models available</option>
              ) : (
                models.map((model: any) => (
                  <option key={model.name || model} value={model.name || model}>
                    {model.name || model}
                  </option>
                ))
              )}
            </select>

            <Button
              className="w-full"
              onClick={handleInitializeChat}
              disabled={
                isInitializing || isLoadingModels || models.length === 0 || apiConnected !== true
              }
            >
              {isInitializing ? 'Initializing...' : 'Start Chat'}
            </Button>
          </div>
        </div>
      ) : (
        <>
          {/* Chat header */}
          <div className="sticky top-0 z-10 flex items-center justify-between p-4 border-b bg-[hsl(var(--card))] border-[hsl(var(--border))]">
            <div>
              <h2 className="font-medium">Chat with {session.model}</h2>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">Session: {session.id}</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSession(null)
                setMessages([])
              }}
            >
              New Chat
            </Button>
          </div>

          {/* Messages container */}
          <div className="flex-1 p-4 overflow-y-auto">
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      message.role === 'user'
                        ? 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]'
                        : 'bg-[hsl(var(--card))] border border-[hsl(var(--border))]'
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{message.content}</div>
                    <div className="mt-1 text-xs opacity-70">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input area */}
          <div className="sticky bottom-0 p-4 border-t bg-[hsl(var(--background))] border-[hsl(var(--border))]">
            <div className="flex gap-2 max-w-4xl mx-auto">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message here..."
                disabled={isSending}
                className="flex-1"
              />
              <Button onClick={sendMessage} disabled={isSending || !input.trim()}>
                {isSending ? '...' : 'Send'}
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default ChatApp
