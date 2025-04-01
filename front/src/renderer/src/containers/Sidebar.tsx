import React, { useState, useEffect } from 'react'
import { Input } from '../components/ui/input'
import { Button } from '../components/ui/button'
import { Search, PlusCircle, MessageSquare, Wrench, Settings, Bot, Loader2 } from 'lucide-react'
import ollamaLogo from '../assets/ollama.png'
import { useChatStore } from '../store/chatStore'
import { useInitializeChat, useAvailableChats, useSearchChats } from '../fetch/queries'
import { APIChat, DisplayedChatSession } from '../fetch/types'

const Sidebar: React.FC = () => {
  const [activeChat, setActiveChat] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [paginationState] = useState({
    limit: 50,
    offset: 0,
    includeInactive: false
  })

  const sessionId = useChatStore((state) => state.sessionId)
  const setSessionId = useChatStore((state) => state.setSessionId)
  const setModelName = useChatStore((state) => state.setModelName)
  const setSessionActive = useChatStore((state) => state.setSessionActive)
  const selectedModel = useChatStore((state) => state.selectedModel)

  useEffect(() => {
    if (sessionId) {
      setActiveChat(sessionId)
    }
  }, [sessionId])

  const {
    data: availableChatsData,
    isLoading: isLoadingChats,
    isError: isChatsError
  } = useAvailableChats(
    paginationState.includeInactive,
    paginationState.limit,
    paginationState.offset
  )

  const {
    data: searchChatsData,
    isLoading: isSearchingChats,
    isError: isSearchError
  } = useSearchChats(
    searchQuery,
    paginationState.includeInactive,
    paginationState.limit,
    paginationState.offset
  )

  const { mutate: initializeChat, isPending: isInitializing } = useInitializeChat()

  const formatDate = (date: Date): string => {
    return new Date(date).toLocaleDateString([], {
      month: 'short',
      day: 'numeric'
    })
  }

  const convertApiChatToDisplayChat = (apiChat: APIChat): DisplayedChatSession => {
    return {
      id: apiChat.session_id,
      title: `Chat with ${apiChat.model_name}`,
      lastMessage: apiChat.last_message_time
        ? `Last active ${formatDate(new Date(apiChat.last_active))}`
        : 'No messages yet',
      timestamp: apiChat.last_message_time
        ? new Date(apiChat.last_message_time)
        : new Date(apiChat.created_at),
      messageCount: apiChat.message_count
    }
  }

  const displayedChats: DisplayedChatSession[] =
    searchQuery && searchQuery.trim().length > 0
      ? (searchChatsData?.sessions || []).map(convertApiChatToDisplayChat)
      : (availableChatsData?.sessions || []).map(convertApiChatToDisplayChat)

  const handleNewChat = (): void => {
    initializeChat({
      model_name: selectedModel,
      system_message: 'You are a helpful assistant.'
    })
  }

  const handleChatClick = (chatSession: DisplayedChatSession): void => {
    setActiveChat(chatSession.id)

    const apiChat =
      searchQuery && searchQuery.trim().length > 0
        ? searchChatsData?.sessions.find((s) => s.session_id === chatSession.id)
        : availableChatsData?.sessions.find((s) => s.session_id === chatSession.id)

    if (apiChat) {
      setSessionId(apiChat.session_id)
      setModelName(apiChat.model_name)
      setSessionActive(true)
    }
  }

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    setSearchQuery(e.target.value)
  }

  return (
    <div className="flex flex-col h-screen w-64 bg-white border-r border-gray-200">
      <div className="p-4 flex items-center">
        <div className="font-bold text-xl flex items-center">
          <img src={ollamaLogo} alt="Ollama Logo" className="w-6 h-6 mr-1" />
          ollama desktop
        </div>
      </div>
      <div className="px-4 mb-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
          <Input
            type="text"
            placeholder="Search chats"
            className="pl-8 bg-gray-100 border-0 h-9"
            value={searchQuery}
            onChange={handleSearchChange}
          />
        </div>
      </div>
      <div className="px-4 mb-4">
        <Button
          onClick={handleNewChat}
          className="w-full justify-start bg-white hover:bg-gray-50 text-black border border-gray-200"
          disabled={isInitializing}
        >
          {isInitializing ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Creating...
            </>
          ) : (
            <>
              <PlusCircle className="h-4 w-4 mr-2" />
              New Chat
            </>
          )}
        </Button>
      </div>
      <div className="flex-grow overflow-y-auto px-2">
        <div className="flex justify-between items-center px-2 mb-2">
          <h3 className="text-xs font-semibold text-gray-600">
            {searchQuery ? 'Search Results' : 'Available Chats'}
          </h3>
          {(isLoadingChats || isSearchingChats) && (
            <Loader2 className="h-3 w-3 animate-spin text-gray-400" />
          )}
        </div>

        {(isChatsError || isSearchError) && (
          <div className="p-2 bg-red-50 text-red-600 rounded-lg text-xs mx-2">
            Error: Failed to load chats
          </div>
        )}

        {displayedChats.length === 0 ? (
          <div className="text-xs text-gray-500 px-2">
            {searchQuery
              ? 'No matching chats found. Try a different search term.'
              : 'No chats available. Start a new chat to begin.'}
          </div>
        ) : (
          displayedChats.map((chat) => (
            <div
              key={chat.id}
              onClick={() => handleChatClick(chat)}
              className={`flex flex-col p-2 rounded-lg cursor-pointer mb-1 ${
                activeChat === chat.id || sessionId === chat.id ? 'bg-gray-100' : 'hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center">
                <MessageSquare className="h-4 w-4 mr-2 text-gray-500 flex-shrink-0" />
                <span className="text-sm text-gray-700 font-medium truncate">{chat.title}</span>
              </div>

              <div className="ml-6 mt-1">
                <div className="flex justify-between">
                  <p className="text-xs text-gray-500 truncate">{chat.messageCount} messages</p>
                  {chat.timestamp && (
                    <p className="text-xs text-gray-400">{formatDate(chat.timestamp)}</p>
                  )}
                </div>
                {chat.lastMessage && (
                  <p className="text-xs text-gray-500 truncate">{chat.lastMessage}</p>
                )}
              </div>
            </div>
          ))
        )}
      </div>
      <div className="p-2 space-y-1 border-t border-gray-200">
        <div className="flex items-center p-2 rounded-lg cursor-pointer hover:bg-gray-50">
          <Wrench className="h-4 w-4 mr-2 text-gray-500" />
          <span className="text-sm text-gray-700">MCP Servers</span>
        </div>
        <div className="flex items-center p-2 rounded-lg cursor-pointer hover:bg-gray-50">
          <Bot className="h-4 w-4 mr-2 text-gray-500" />
          <span className="text-sm text-gray-700">Agents</span>
        </div>
        <div className="flex items-center p-2 rounded-lg cursor-pointer hover:bg-gray-50">
          <Settings className="h-4 w-4 mr-2 text-gray-500" />
          <span className="text-sm text-gray-700">Settings</span>
        </div>
      </div>
    </div>
  )
}

export default Sidebar
