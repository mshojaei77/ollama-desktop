import { useState, useEffect, useRef } from 'react'
import { Input } from '@renderer/components/ui/input'
import { Button } from '@renderer/components/ui/button'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import 'highlight.js/styles/github.css'
import '../styles/markdown.css'
import {
  useModels,
  useInitializeChat,
  useSendMessage,
  checkApiConnection,
  useChatHistory
} from '../fetch/queries'
import { useChatStore } from '../store/chatStore'
import { queryClient } from '../fetch/queries'
import { getIconPath, copyToClipboardWithFeedback } from '../utils'
import { ModelsDropdown } from '../components/ModelsDropdown'
import { MessageActions } from '../components/MessageActions'

export default function Chat(): JSX.Element {
  const [input, setInput] = useState('')
  const [apiConnected, setApiConnected] = useState<boolean | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const messages = useChatStore((state) => state.messages)
  const sessionId = useChatStore((state) => state.sessionId)
  const selectedModel = useChatStore((state) => state.selectedModel)
  const isSessionActive = useChatStore((state) => state.isSessionActive)
  const setSelectedModel = useChatStore((state) => state.setSelectedModel)
  const setMessages = useChatStore((state) => state.setMessages)
  const clearMessages = useChatStore((state) => state.clearMessages)

  const {
    data: chatHistoryData,
    isLoading: isLoadingHistory,
    error: historyError,
    refetch: refetchHistory
  } = useChatHistory(sessionId)

  useEffect(() => {
    const checkConnection = async (): Promise<void> => {
      const isConnected = await checkApiConnection()
      setApiConnected(isConnected)
    }

    checkConnection()
  }, [])

  useEffect(() => {
    if (chatHistoryData && chatHistoryData.history) {
      clearMessages()

      const formattedMessages = chatHistoryData.history.map((msg) => ({
        id: msg.id,
        role: msg.role,
        content: msg.message,
        timestamp: new Date(msg.timestamp)
      }))

      setTimeout(() => {
        setMessages(formattedMessages)
      }, 0)
    }
  }, [chatHistoryData, setMessages, clearMessages])

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  useEffect(() => {
    if (sessionId) {
      queryClient.invalidateQueries({ queryKey: ['chatHistory', sessionId] })
    } else {
      clearMessages()
    }
  }, [sessionId, clearMessages, refetchHistory])

  const {
    data: models = [],
    isLoading: isLoadingModels,
    error: modelsError
  } = useModels(apiConnected === true)

  const { mutate: initializeChat, isPending: isInitializing } = useInitializeChat()

  const { mutate: sendMessageMutation, isPending: isSending } = useSendMessage()

  const handleInitializeChat = (): void => {
    initializeChat({
      model_name: selectedModel,
      system_message: 'You are a helpful assistant.'
    })
  }

  const sendMessage = (): void => {
    if (!input.trim() || !sessionId) return

    setInput('')

    sendMessageMutation({
      message: input,
      session_id: sessionId
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const copyToClipboard = (content: string): void => {
    navigator.clipboard
      .writeText(content)
      .then(() => {
        console.log('Content copied to clipboard')
      })
      .catch((err) => {
        console.error('Failed to copy:', err)
      })
  }

  const regenerateResponse = (messageId: string): void => {
    const messageIndex = messages.findIndex((m) => m.id === messageId)
    if (messageIndex < 1 || !sessionId) return

    const userMessageIndex = messageIndex - 1
    const userMessage = messages[userMessageIndex]

    sendMessageMutation({
      message: userMessage.content,
      session_id: sessionId
    })
  }

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
      {!isSessionActive ? (
        <div className="flex flex-col items-center justify-center h-full p-6">
          <div className="w-full max-w-md rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-8 shadow-sm">
            <div className="text-center mb-6">
              <div className="flex justify-center mb-4">
                <img
                  src={new URL('../assets/ollama-logo.png', import.meta.url).href}
                  alt="Ollama Logo"
                  className="h-14 w-auto"
                  onError={(e) => {
                    // Fallback if logo doesn't exist
                    e.currentTarget.style.display = 'none'
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
                  <span className="ml-2 text-sm text-[hsl(var(--muted-foreground))]">
                    Loading available models...
                  </span>
                </div>
              )}

              <div className="flex flex-col items-center space-y-3">
                <label className="text-sm font-medium">Select a model to start chatting</label>
                <div className="w-3/4 mx-auto">
                  <ModelsDropdown
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
            {isLoadingHistory && (
              <div className="flex justify-center my-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                <span className="ml-2 text-sm text-gray-500">Loading chat history...</span>
              </div>
            )}

            {historyError && (
              <div className="mx-auto max-w-4xl my-4 p-3 border rounded-lg border-red-300 bg-red-50 text-red-700">
                <p>
                  Error loading chat history:{' '}
                  {historyError instanceof Error ? historyError.message : 'Unknown error'}
                </p>
                <button
                  onClick={() => refetchHistory()}
                  className="mt-2 text-sm text-blue-600 hover:underline"
                >
                  Try again
                </button>
              </div>
            )}

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
                            e.currentTarget.src = new URL(
                              '../assets/models/default.png',
                              import.meta.url
                            ).href
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
                              code: ({ className, children, ...props }) => {
                                const match = /language-(\w+)/.exec(className || '')
                                if (match) {
                                  return (
                                    <div className="code-block-wrapper">
                                      <div className="code-block-header">
                                        <span>{match[1]}</span>
                                        <button
                                          onClick={(e) => {
                                            const content = String(children).replace(/\n$/, '')
                                            copyToClipboardWithFeedback(content, e.currentTarget)
                                          }}
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
                                  )
                                }
                                return (
                                  <code className={className} {...props}>
                                    {children}
                                  </code>
                                )
                              },
                              a: (props) => (
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
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="12"
                        height="12"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                      </svg>
                      <span>auto</span>
                    </div>

                    <div className="relative">
                      <ModelsDropdown
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
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
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
