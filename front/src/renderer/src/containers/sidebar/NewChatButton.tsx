import { PlusCircle } from 'lucide-react'
import { Button } from '@renderer/components/ui/button'
import { useNavigate } from 'react-router-dom'
import { Routes } from '@renderer/lib/routes'
import { useChatStore } from '@renderer/store/chatStore'

const NewChatButton = (): JSX.Element => {
  const navigate = useNavigate()
  const clearMessages = useChatStore((state) => state.clearMessages)
  const setSessionActive = useChatStore((state) => state.setSessionActive)
  const setSessionId = useChatStore((state) => state.setSessionId)

  const handleNewChat = (): void => {
    // Reset chat session and navigate to welcome page
    clearMessages()
    setSessionActive(false)
    setSessionId(null)
    navigate(Routes.HOME)
  }

  return (
    <div className="px-4 mb-4">
      <Button
        onClick={handleNewChat}
        className="w-full justify-start bg-[hsl(var(--card))] hover:bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] border border-[hsl(var(--border))]"
      >
        <PlusCircle className="h-4 w-4 mr-2" />
        New Chat
      </Button>
    </div>
  )
}

export default NewChatButton
