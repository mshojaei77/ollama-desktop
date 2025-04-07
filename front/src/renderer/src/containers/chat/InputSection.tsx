import { Input } from '@renderer/components/ui/input'
import { ModelsDropdown } from '@renderer/components/ModelsDropdown'
import { useChatStore } from '@renderer/store/chatStore'
import { useModels, useSendMessage } from '@renderer/fetch/queries'
import { useState } from 'react'
const InputSection = ({ apiConnected }: { apiConnected: boolean }): JSX.Element => {
  const [input, setInput] = useState('')
  const sessionId = useChatStore((state) => state.sessionId)
  const selectedModel = useChatStore((state) => state.selectedModel)
  const setSelectedModel = useChatStore((state) => state.setSelectedModel)
  const { data: models = [], isLoading: isLoadingModels } = useModels(apiConnected === true)
  const [toolsEnabled, setToolsEnabled] = useState(false)

  const { mutate: sendMessageMutation, isPending: isSending } = useSendMessage()

  const handleKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const sendMessage = (): void => {
    if (!input.trim() || !sessionId) return

    setInput('')

    sendMessageMutation({
      message: input,
      session_id: sessionId
    })
  }

  return (
    <div className="sticky bottom-0 p-4 bg-[hsl(var(--background))]">
      <div className="flex flex-col w-full bg-[hsl(var(--card))] rounded-2xl py-3 border border-[hsl(var(--border))] shadow-sm">
        <div className="px-4">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything"
            disabled={isSending}
            className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0 bg-transparent w-full text-sm px-0 placeholder-[hsl(var(--muted-foreground))]"
          />
        </div>
        
        <div className="flex items-center gap-2 mt-1">
          <div className="pl-2">
            <ModelsDropdown
              models={models}
              selectedModel={selectedModel}
              onChange={(value) => setSelectedModel(value)}
              isLoading={isLoadingModels}
              disabled={apiConnected !== true}
            />
          </div>

          <div className="flex items-center gap-2 ml-auto pr-4">
            <button 
              onClick={() => setToolsEnabled(!toolsEnabled)}
              className={`p-1.5 ${toolsEnabled ? 'text-blue-600' : 'text-[hsl(var(--muted-foreground))]'} hover:text-[hsl(var(--foreground))]`}
              title={toolsEnabled ? "Disable tools" : "Enable tools"}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
              </svg>
            </button>

            <button className="p-1.5 text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
              </svg>
            </button>

            <button
              onClick={sendMessage}
              disabled={isSending || !input.trim()}
              className="p-1.5 text-blue-600 hover:text-blue-700 disabled:opacity-50"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
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
    </div>
  )
}

export default InputSection
