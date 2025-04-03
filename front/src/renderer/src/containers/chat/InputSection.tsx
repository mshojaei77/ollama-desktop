import { Input } from '@renderer/components/ui/input'
import { ModelsDropdown } from '@renderer/components/ModelsDropdown'
import { useChatStore } from '@renderer/store/chatStore'
import { useModels, useSendMessage } from '@renderer/fetch/queries'
import { useState } from 'react'
const InputSection = ({ apiConnected }: { apiConnected: boolean }): JSX.Element => {
  const [input, setInput] = useState('')
  const [webSearchEnabled, setWebSearchEnabled] = useState(false)
  const sessionId = useChatStore((state) => state.sessionId)
  const selectedModel = useChatStore((state) => state.selectedModel)
  const setSelectedModel = useChatStore((state) => state.setSelectedModel)
  const { data: models = [], isLoading: isLoadingModels } = useModels(apiConnected === true)

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
      session_id: sessionId,
      web_search: webSearchEnabled
    })
  }

  const toggleWebSearch = (): void => {
    setWebSearchEnabled(!webSearchEnabled)
  }

  return (
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
              <button
                onClick={toggleWebSearch}
                className={`flex items-center justify-center w-8 h-8 text-sm border rounded-full transition-colors ${
                  webSearchEnabled ? 'bg-blue-100 text-blue-700 border-blue-300' : 'bg-gray-100 text-gray-700 border-gray-200'
                }`}
                title={webSearchEnabled ? "Web search enabled - AI will search the internet for answers" : "Web search disabled - AI will use only its knowledge"}
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
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="2" y1="12" x2="22" y2="12"></line>
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                </svg>
              </button>

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
  )
}

export default InputSection
