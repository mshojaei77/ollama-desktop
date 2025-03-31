import { useState, useEffect, useRef } from 'react'
import { Input } from '@renderer/components/ui/input'
import { Button } from '@renderer/components/ui/button'
import axios from 'axios'
import { useQuery, useMutation, QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import 'highlight.js/styles/github.css'
import '@renderer/styles/markdown.css'

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

// Add new interfaces for message reactions
interface MessageReaction {
  count: number;
  reacted: boolean;
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  // Add reactions tracking
  reactions?: {
    likes?: MessageReaction;
    dislikes?: MessageReaction;
  }
}

interface ChatSession {
  id: string
  model: string
}

// Utility to extract base model name (e.g., "llama" from "llama3.2:latest" or "llama 3.3 70b")
const getModelBaseName = (modelName: string): string => {
  // Special case: if model name contains "embed", use the embed icon
  if (modelName.toLowerCase().includes('embed')) {
    return 'embed';
  }
  
  // First remove any tag after a colon (e.g., ":latest")
  const nameWithoutTag = modelName.split(':')[0];
  
  // If there's a username/repo format, take only the repo part
  const repoName = nameWithoutTag.includes('/') ? nameWithoutTag.split('/')[1] : nameWithoutTag;
  
  // If the name has spaces, take the first part (like "llama" from "llama 3.3 70b")
  if (repoName.includes(' ')) {
    return repoName.split(' ')[0].toLowerCase();
  }
  
  // If the name has hyphens, take the first part (like "gemma" from "gemma-3-4b-persian-v0")
  if (repoName.includes('-')) {
    return repoName.split('-')[0].toLowerCase();
  }
  
  // Otherwise, extract the alphabetic prefix (like "llama" from "llama3.2")
  const match = repoName.match(/^([a-zA-Z]+)/);
  if (match && match[1]) {
    return match[1].toLowerCase();
  }
  
  // Fallback to the original name
  return repoName.toLowerCase();
}

// Helper function to get icon path for a model
const getIconPath = (modelName: string) => {
  const baseName = getModelBaseName(modelName);
  try {
    // Try to dynamically import the icon
    return new URL(`../assets/models/${baseName}.png`, import.meta.url).href;
  } catch (error) {
    // Fallback to default icon
    return new URL('../assets/models/default.png', import.meta.url).href;
  }
};

// Add this helper function to get display name for models
const getModelDisplayName = (modelName: string): string => {
  // If model has a username/repo format, display only the repo part
  if (modelName.includes('/')) {
    return modelName.split('/')[1];
  }
  
  return modelName;
}

// Component for model dropdown with icons
interface ModelOption {
  name: string;
  description?: string;
}

const ModelDropdown = ({
  models,
  selectedModel,
  onChange,
  isLoading,
  disabled
}: {
  models: ModelOption[] | string[];
  selectedModel: string;
  onChange: (value: string) => void;
  isLoading: boolean;
  disabled: boolean;
}) => {
  // Format models array to ensure consistent structure
  const formattedModels = models.map(model => {
    if (typeof model === 'string') {
      return { name: model, description: `AI model` };
    }
    return model;
  });

  return (
    <div className="relative min-w-[150px] max-w-[300px]">
      <select
        className="w-full p-2 pl-10 border rounded-full bg-[hsl(var(--background))] border-[hsl(var(--input))] appearance-none cursor-pointer overflow-hidden text-ellipsis"
        value={selectedModel}
        onChange={(e) => onChange(e.target.value)}
        disabled={isLoading || disabled}
        title={selectedModel} // Show full name on hover
      >
        {isLoading ? (
          <option>Loading models...</option>
        ) : formattedModels.length === 0 ? (
          <option>No models available</option>
        ) : (
          formattedModels.map((model) => (
            <option key={model.name} value={model.name} title={model.name}>
              {getModelDisplayName(model.name)}
            </option>
          ))
        )}
      </select>

      {/* We'll render the selected model with icon above the select for visual styling */}
      {!isLoading && selectedModel && (
        <div className="absolute inset-y-0 left-0 flex items-center pl-2 pointer-events-none">
          <img 
            src={getIconPath(selectedModel)} 
            alt=""
            className="w-6 h-6 rounded-full"
            onError={(e) => {
              // Fallback to default icon if the specific icon fails to load
              e.currentTarget.src = new URL('../assets/models/default.png', import.meta.url).href;
            }}
          />
        </div>
      )}
      
      {/* Custom dropdown arrow */}
      <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m6 9 6 6 6-6"/>
        </svg>
      </div>
    </div>
  );
};

// Add new component for message action buttons
const MessageActions = ({ message, onCopy, onRefresh, onLike, onDislike, onShare }) => {
  return (
    <div className="flex items-center gap-2 mt-1">
      <button onClick={() => onCopy(message.content)} className="p-1 text-gray-500 hover:text-gray-700" title="Copy to clipboard">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
      </button>
      <button onClick={() => onRefresh(message.id)} className="p-1 text-gray-500 hover:text-gray-700" title="Regenerate response">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"></path>
        </svg>
      </button>
      <button 
        onClick={() => onLike(message.id)} 
        className={`p-1 ${message.reactions?.likes?.reacted ? 'text-blue-500' : 'text-gray-500 hover:text-gray-700'}`}
        title="Like"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
        </svg>
      </button>
      <button 
        onClick={() => onDislike(message.id)} 
        className={`p-1 ${message.reactions?.dislikes?.reacted ? 'text-red-500' : 'text-gray-500 hover:text-gray-700'}`}
        title="Dislike"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm10-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path>
        </svg>
      </button>
      <button onClick={() => onShare(message.id)} className="p-1 text-gray-500 hover:text-gray-700" title="Share">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="18" cy="5" r="3"></circle>
          <circle cx="6" cy="12" r="3"></circle>
          <circle cx="18" cy="19" r="3"></circle>
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
          <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
        </svg>
      </button>
    </div>
  );
};

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
          content: `Hello! I'm ${data.model}. How can I help you today?`,
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

  // Add new state and handlers for message reactions
  const copyToClipboard = (content: string) => {
    navigator.clipboard.writeText(content);
    // You could add a toast notification here
  };

  const regenerateResponse = (messageId: string) => {
    // Find the last user message before this assistant message
    const messageIndex = messages.findIndex(m => m.id === messageId);
    if (messageIndex < 1) return;
    
    // Assuming assistant messages always follow user messages
    const userMessageIndex = messageIndex - 1;
    const userMessage = messages[userMessageIndex];
    
    // Send this message again
    if (session) {
      sendMessageMutation({
        message: userMessage.content,
        session_id: session.id
      });
    }
  };

  const handleLike = (messageId: string) => {
    setMessages(messages.map(msg => 
      msg.id === messageId ? 
      {
        ...msg, 
        reactions: {
          ...msg.reactions,
          likes: { count: (msg.reactions?.likes?.count || 0) + (msg.reactions?.likes?.reacted ? -1 : 1), reacted: !msg.reactions?.likes?.reacted },
          dislikes: { ...msg.reactions?.dislikes, reacted: false } // Reset dislike if liked
        }
      } : msg
    ));
  };

  const handleDislike = (messageId: string) => {
    setMessages(messages.map(msg => 
      msg.id === messageId ? 
      {
        ...msg, 
        reactions: {
          ...msg.reactions,
          dislikes: { count: (msg.reactions?.dislikes?.count || 0) + (msg.reactions?.dislikes?.reacted ? -1 : 1), reacted: !msg.reactions?.dislikes?.reacted },
          likes: { ...msg.reactions?.likes, reacted: false } // Reset like if disliked
        }
      } : msg
    ));
  };

  const handleShare = (messageId: string) => {
    // Share functionality would go here
    // Could open a modal or copy a shareable link
    const message = messages.find(m => m.id === messageId);
    if (message) {
      copyToClipboard(message.content);
      // Show a toast notification
    }
  };

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
        <div className="flex flex-col items-center justify-center h-full p-6">
          {/* Enhanced welcome screen with better branding */}
          <div className="w-full max-w-md rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-8 shadow-sm">
            <div className="text-center mb-6">
              {/* Add logo */}
              <div className="flex justify-center mb-4">
                <img 
                  src={new URL('../assets/ollama-logo.png', import.meta.url).href}
                  alt="Ollama Logo" 
                  className="h-14 w-auto"
                  onError={(e) => {
                    // Fallback if logo doesn't exist
                    e.currentTarget.style.display = 'none';
                  }}
                />
              </div>
              <h1 className="text-3xl font-bold mb-2">Welcome to Ollama Chat</h1>
              <p className="text-[hsl(var(--muted-foreground))]">
                Chat with AI models running locally on your machine
              </p>
            </div>

            <div className="space-y-6">
              {modelsError ? (
                <div className="p-3 mb-4 border rounded border-red-300 bg-red-50 text-red-700">
                  <p className="font-medium">Error loading models</p>
                  <p className="text-sm">
                    {modelsError instanceof Error ? modelsError.message : 'Please try again later.'}
                  </p>
                </div>
              ) : null}
              
              {/* Add loading indicator */}
              {isLoadingModels && (
                <div className="flex justify-center items-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[hsl(var(--primary))]"></div>
                  <span className="ml-2 text-sm text-[hsl(var(--muted-foreground))]">Loading available models...</span>
                </div>
              )}

              <div className="flex flex-col items-center space-y-3">
                <label className="text-sm font-medium">
                  Select a model to start chatting
                </label>
                <div className="w-3/4 mx-auto">
                  <ModelDropdown
                    models={models}
                    selectedModel={selectedModel}
                    onChange={(value) => setSelectedModel(value)}
                    isLoading={isLoadingModels}
                    disabled={apiConnected !== true}
                  />
                </div>
              </div>

              <Button
                className="w-full py-6 text-base font-medium rounded-lg"
                onClick={handleInitializeChat}
                disabled={
                  isInitializing || isLoadingModels || models.length === 0 || apiConnected !== true
                }
              >
                {isInitializing ? (
                  <>
                    <span className="animate-spin mr-2 h-4 w-4 border-2 border-current border-t-transparent rounded-full"></span>
                    Initializing...
                  </>
                ) : (
                  'Start Chat'
                )}
              </Button>
              
              {/* Add helpful tips */}
              <div className="mt-6 border-t pt-4 border-[hsl(var(--border))]">
                <h3 className="text-sm font-medium mb-2">Tips:</h3>
                <ul className="text-xs text-[hsl(var(--muted-foreground))] space-y-1 list-disc pl-4">
                  <li>Models run locally on your machine</li>
                  <li>Conversations are private and not shared</li>
                  <li>Different models have different capabilities</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* Messages container - Update with markdown rendering */}
          <div className="flex-1 p-4 overflow-y-auto">
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 mr-2">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600">
                        <img 
                          src={getIconPath(selectedModel)} 
                          alt=""
                          className="w-6 h-6 rounded-full"
                          onError={(e) => {
                            // Fallback to default icon
                            e.currentTarget.src = new URL('../assets/models/default.png', import.meta.url).href;
                          }}
                        />
                      </div>
                    </div>
                  )}
                  
                  <div className="flex flex-col max-w-[80%]">
                    <div
                      className={`rounded-2xl p-3 ${
                        message.role === 'user'
                          ? 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]'
                          : 'bg-[hsl(var(--card))] border border-[hsl(var(--border))]'
                      }`}
                    >
                      {message.role === 'user' ? (
                        // User messages remain as plain text with whitespace preserved
                        <div className="whitespace-pre-wrap">{message.content}</div>
                      ) : (
                        // Assistant messages rendered as markdown
                        <div className="markdown-content">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeHighlight]}
                            components={{
                              // Customize code blocks
                              code({node, inline, className, children, ...props}) {
                                const match = /language-(\w+)/.exec(className || '')
                                return !inline && match ? (
                                  <div className="code-block-wrapper">
                                    <div className="code-block-header">
                                      <span>{match[1]}</span>
                                      <button 
                                        onClick={() => copyToClipboard(String(children).replace(/\n$/, ''))}
                                        className="code-copy-button"
                                      >
                                        Copy
                                      </button>
                                    </div>
                                    <pre className={className}>
                                      <code className={className} {...props}>
                                        {children}
                                      </code>
                                    </pre>
                                  </div>
                                ) : (
                                  <code className={className} {...props}>
                                    {children}
                                  </code>
                                )
                              },
                              // Style links to open in new tab
                              a: ({node, ...props}) => (
                                <a 
                                  target="_blank" 
                                  rel="noopener noreferrer" 
                                  className="text-blue-500 hover:underline"
                                  {...props}
                                />
                              )
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>
                    
                    {message.role === 'assistant' && (
                      <MessageActions 
                        message={message}
                        onCopy={copyToClipboard}
                        onRefresh={regenerateResponse}
                        onLike={handleLike}
                        onDislike={handleDislike}
                        onShare={handleShare}
                      />
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input area - Update to match UI */}
          <div className="sticky bottom-0 p-4 border-t bg-[hsl(var(--background))] border-[hsl(var(--border))]">
            <div className="flex justify-between max-w-4xl mx-auto relative">
              <div className="flex items-center w-full gap-3">
                <div className="flex items-center border rounded-full bg-white px-4 py-2 flex-1">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask anything"
                    disabled={isSending}
                    className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0 px-0"
                  />
                  
                  <div className="flex items-center gap-2 ml-2">
                    <div className="flex items-center gap-1 text-sm border rounded-full px-2 py-1 bg-gray-100">
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                      </svg>
                      <span>auto</span>
                    </div>
                    
                    <div className="relative">
                      <ModelDropdown
                        models={models}
                        selectedModel={selectedModel}
                        onChange={(value) => setSelectedModel(value)}
                        isLoading={isLoadingModels}
                        disabled={apiConnected !== true}
                      />
                    </div>
                  </div>
                </div>
                
                <button 
                  onClick={sendMessage} 
                  disabled={isSending || !input.trim()} 
                  className="w-10 h-10 flex items-center justify-center rounded-full bg-blue-500 text-white disabled:opacity-50"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="12" y1="19" x2="12" y2="5"></line>
                    <polyline points="5 12 12 5 19 12"></polyline>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default ChatApp
