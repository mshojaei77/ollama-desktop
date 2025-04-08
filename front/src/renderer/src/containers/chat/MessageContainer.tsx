import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { getIconPath, copyToClipboardWithFeedback } from '../../utils'
import { MessageActions } from '../../components/MessageActions'
import { useChatStore } from '@renderer/store/chatStore'
import { queryClient, useChatHistory, useSendMessage } from '@renderer/fetch/queries'
import { useEffect, useRef, useState } from 'react'
import { copyToClipboard } from '../../utils'

const MessageContainer = (): JSX.Element => {
  const sessionId = useChatStore((state) => state.sessionId)
  const messages = useChatStore((state) => state.messages)
  const setMessages = useChatStore((state) => state.setMessages)
  const clearMessages = useChatStore((state) => state.clearMessages)
  const selectedModel = useChatStore((state) => state.selectedModel)
  
  const [isStreaming, setIsStreaming] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const lastScrollHeightRef = useRef<number>(0)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  const {
    data: chatHistoryData,
    isLoading: isLoadingHistory,
    error: historyError,
    refetch: refetchHistory
  } = useChatHistory(sessionId)

  const { mutate: sendMessageMutation, isPending: isSendingMessage, isError: isSendError } = useSendMessage()

  // Debug logging for messages
  useEffect(() => {
    console.log('Current messages:', messages)
    
    // Debug specific message content
    messages.forEach(message => {
      if (message.role === 'assistant') {
        console.log('Assistant message details:', {
          id: message.id,
          contentLength: message.content?.length || 0,
          content: message.content?.substring(0, 50) + (message.content?.length > 50 ? '...' : ''),
          contentExists: !!message.content
        });
      }
    });
  }, [messages])

  useEffect(() => {
    // Update streaming state based on message sending status
    console.log('Message sending status changed:', { isSendingMessage, isSendError })
    setIsStreaming(isSendingMessage)
  }, [isSendingMessage, isSendError])

  useEffect(() => {
    if (chatHistoryData && chatHistoryData.history) {
      console.log('Received chat history:', chatHistoryData)
      clearMessages()

      const formattedMessages = chatHistoryData.history.map((msg) => ({
        id: msg.id,
        role: msg.role,
        content: msg.message,
        timestamp: new Date(msg.timestamp)
      }))

      console.log('Formatted messages from history:', formattedMessages)
      setTimeout(() => {
        setMessages(formattedMessages)
      }, 0)
    }
  }, [chatHistoryData, setMessages, clearMessages])

  // Smart scrolling behavior that respects user scrolling during streaming
  useEffect(() => {
    if (!messagesEndRef.current || !scrollContainerRef.current) return
    
    const scrollContainer = scrollContainerRef.current
    const currentScrollHeight = scrollContainer.scrollHeight
    const isUserScrolledUp = scrollContainer.scrollTop + scrollContainer.clientHeight < lastScrollHeightRef.current - 30
    
    // Scroll to bottom in these cases:
    // 1. New message added (height changed significantly)
    // 2. Currently streaming and user hasn't scrolled up
    const shouldScrollToBottom = 
      currentScrollHeight !== lastScrollHeightRef.current || 
      (isStreaming && !isUserScrolledUp)
    
    console.log('Scroll state:', { 
      currentHeight: currentScrollHeight, 
      lastHeight: lastScrollHeightRef.current, 
      isStreaming,
      isUserScrolledUp,
      shouldScrollToBottom
    })
      
    if (shouldScrollToBottom) {
      messagesEndRef.current.scrollIntoView({ behavior: isStreaming ? 'auto' : 'smooth' })
    }
    
    lastScrollHeightRef.current = currentScrollHeight
  }, [messages, isStreaming])

  useEffect(() => {
    if (sessionId) {
      console.log('Invalidating chat history for session:', sessionId)
      queryClient.invalidateQueries({ queryKey: ['chatHistory', sessionId] })
    } else {
      clearMessages()
    }
  }, [sessionId, clearMessages])

  const regenerateResponse = (messageId: string): void => {
    const messageIndex = messages.findIndex((m) => m.id === messageId)
    if (messageIndex < 1 || !sessionId) return

    const userMessageIndex = messageIndex - 1
    const userMessage = messages[userMessageIndex]

    console.log('Regenerating response for message:', messageId, 'using user message:', userMessage)

    // Remove the assistant message that will be regenerated
    const updatedMessages = [...messages]
    updatedMessages.splice(messageIndex, 1)
    setMessages(updatedMessages)
    
    // Send the message again to trigger regeneration
    sendMessageMutation({
      message: userMessage.content,
      session_id: sessionId
    })
  }

  return (
    <div 
      ref={scrollContainerRef} 
      className="flex-1 p-4 overflow-y-auto px-20 hide-scrollbar"
    >
      {isLoadingHistory && (
        <div className="flex justify-center my-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          <span className="ml-2 text-sm text-[hsl(var(--muted-foreground))]">Loading chat history...</span>
        </div>
      )}

      {historyError && (
        <div className="mx-auto max-w-4xl my-4 p-3 border rounded-lg border-red-300 bg-[hsl(var(--card))] text-red-700">
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
        {messages.map((message) => {
          const isLastAssistantMessage = 
            message.role === 'assistant' && 
            message.id === messages[messages.length - 1]?.id &&
            isStreaming;
            
          return (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.role === 'assistant' && (
                <div className="flex-shrink-0 mr-2">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-white dark:bg-white text-blue-600 dark:text-blue-600">
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
                        {message.content || ""}
                      </ReactMarkdown>
                    </div>
                  )}
                  {isLastAssistantMessage && (
                    <span className="inline-block ml-1 animate-pulse">▋</span>
                  )}
                </div>
                {message.role === 'assistant' && !isLastAssistantMessage && (
                  <MessageActions
                    message={message}
                    onCopy={copyToClipboard}
                    onRefresh={regenerateResponse}
                  />
                )}
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}

// Add type declaration for window with currentStreamHandler
declare global {
  interface Window {
    currentStreamHandler?: (chunk: string) => void
  }
}

export default MessageContainer
