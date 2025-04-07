import { Loader2, MessageSquare } from 'lucide-react'
import { APIChat, DisplayedChatSession } from '@renderer/fetch/types'
import { useChatStore } from '@renderer/store/chatStore'
import { useAvailableChats, useSearchChats } from '@renderer/fetch/queries'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Routes } from '@renderer/lib/routes'

const AvailableChats = ({ searchQuery }: { searchQuery: string }): JSX.Element => {
  const [paginationState] = useState({
    limit: 50,
    offset: 0,
    includeInactive: false
  })
  const [activeChat, setActiveChat] = useState<string | null>(null)
  const sessionId = useChatStore((state) => state.sessionId)
  const setSessionId = useChatStore((state) => state.setSessionId)
  const setModelName = useChatStore((state) => state.setModelName)
  const setSessionActive = useChatStore((state) => state.setSessionActive)
  const navigate = useNavigate()

  useEffect(() => {
    if (sessionId) {
      setActiveChat(sessionId)
    }
  }, [sessionId])

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

  const {
    data: availableChatsData,
    isLoading: isLoadingChats,
    isError: isChatsError
  } = useAvailableChats(
    paginationState.includeInactive,
    paginationState.limit,
    paginationState.offset
  )

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
      navigate(Routes.HOME)
    }
  }

  return (
    <div className="flex-grow overflow-y-auto px-2 hide-scrollbar">
      <div className="flex justify-between items-center px-2 mb-2">
        <h3 className="text-xs font-semibold text-[hsl(var(--muted-foreground))]">
          {searchQuery ? 'Search Results' : 'Available Chats'}
        </h3>
        {(isLoadingChats || isSearchingChats) && (
          <Loader2 className="h-3 w-3 animate-spin text-[hsl(var(--muted-foreground))]" />
        )}
      </div>

      {(isChatsError || isSearchError) && (
        <div className="p-2 bg-[hsl(var(--destructive))] bg-opacity-10 text-[hsl(var(--destructive))] rounded-lg text-xs mx-2">
          Error: Failed to load chats
        </div>
      )}

      {displayedChats.length === 0 ? (
        <div className="text-xs text-[hsl(var(--muted-foreground))] px-2">
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
              activeChat === chat.id || sessionId === chat.id 
                ? 'bg-[hsl(var(--secondary))]' 
                : 'hover:bg-[hsl(var(--secondary))]'
            }`}
          >
            <div className="flex items-center">
              <MessageSquare className="h-4 w-4 mr-2 text-[hsl(var(--muted-foreground))] flex-shrink-0" />
              <span className="text-sm text-[hsl(var(--foreground))] font-medium truncate">{chat.title}</span>
            </div>

            <div className="ml-6 mt-1">
              <div className="flex justify-between">
                <p className="text-xs text-[hsl(var(--muted-foreground))] truncate">{chat.messageCount} messages</p>
                {chat.timestamp && (
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">{formatDate(chat.timestamp)}</p>
                )}
              </div>
              {chat.lastMessage && (
                <p className="text-xs text-[hsl(var(--muted-foreground))] truncate">{chat.lastMessage}</p>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  )
}

export default AvailableChats
