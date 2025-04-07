import { PlusCircle } from 'lucide-react'
import { Button } from '@renderer/components/ui/button'
import { Loader2 } from 'lucide-react'
import { useInitializeChat } from '@renderer/fetch/queries'
import { useChatStore } from '@renderer/store/chatStore'
import { useNavigate } from 'react-router-dom'
import { Routes } from '@renderer/lib/routes'

const NewChatButton = (): JSX.Element => {
  const selectedModel = useChatStore((state) => state.selectedModel)
  const navigate = useNavigate()

  const { mutate: initializeChat, isPending: isInitializing } = useInitializeChat()

  const handleNewChat = (): void => {
    initializeChat(
      {
        model_name: selectedModel,
        system_message: 'You are a helpful assistant.'
      },
      {
        onSuccess: () => {
          navigate(Routes.HOME)
        }
      }
    )
  }

  return (
    <div className="px-4 mb-4">
      <Button
        onClick={handleNewChat}
        className="w-full justify-start bg-[hsl(var(--card))] hover:bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] border border-[hsl(var(--border))]"
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
  )
}

export default NewChatButton
