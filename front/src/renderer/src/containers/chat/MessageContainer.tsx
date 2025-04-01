import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { getIconPath, copyToClipboardWithFeedback } from '../../utils'
import { MessageActions } from '../../components/MessageActions'
import { useChatStore } from '@renderer/store/chatStore'
import { queryClient, useChatHistory, useSendMessage } from '@renderer/fetch/queries'
import { useEffect, useRef } from 'react'
import { copyToClipboard } from '../../utils'

const MessageContainer = (): JSX.Element => {
  const sessionId = useChatStore((state) => state.sessionId)
  const messages = useChatStore((state) => state.messages)
  const setMessages = useChatStore((state) => state.setMessages)
  const clearMessages = useChatStore((state) => state.clearMessages)
  const selectedModel = useChatStore((state) => state.selectedModel)

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { mutate: sendMessageMutation } = useSendMessage()

  const {
    data: chatHistoryData,
    isLoading: isLoadingHistory,
    error: historyError,
    refetch: refetchHistory
  } = useChatHistory(sessionId)

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

  return (
    <div className="flex-1 p-4 overflow-y-auto px-20">
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
  )
}

export default MessageContainer
