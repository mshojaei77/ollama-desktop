import { PlusCircle } from 'lucide-react'
import { Button } from '@renderer/components/ui/button'
import { Loader2 } from 'lucide-react'
import { useInitializeChat } from '@renderer/fetch/queries'
import { useChatStore } from '@renderer/store/chatStore'

const NewChatButton = (): JSX.Element => {
  const selectedModel = useChatStore((state) => state.selectedModel)

  const { mutate: initializeChat, isPending: isInitializing } = useInitializeChat()

  const handleNewChat = (): void => {
    initializeChat({
      model_name: selectedModel,
      system_message: 'You are a helpful assistant.'
    })
  }

  return (
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
  )
}

export default NewChatButton
