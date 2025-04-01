import { Button } from '../../components/ui/button'
import { ModelsDropdown } from '../../components/ModelsDropdown'
import { useInitializeChat, useModels } from '@renderer/fetch/queries'
import { useChatStore } from '@renderer/store/chatStore'
import ollamaLogo from '../../assets/ollama.png'

const WelcomeNote = ({ apiConnected }: { apiConnected: boolean }): JSX.Element => {
  const selectedModel = useChatStore((state) => state.selectedModel)
  const setSelectedModel = useChatStore((state) => state.setSelectedModel)
  const {
    data: models = [],
    isLoading: isLoadingModels,
    error: modelsError
  } = useModels(apiConnected === true)

  const { mutate: initializeChat, isPending: isInitializing } = useInitializeChat()

  const handleInitializeChat = (): void => {
    initializeChat({
      model_name: selectedModel,
      system_message: 'You are a helpful assistant.'
    })
  }

  return (
    <div className="flex flex-col items-center justify-center h-full p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-6">
          <div className="flex justify-center mb-4">
            <img
              src={ollamaLogo}
              alt="Ollama Logo"
              className="h-18 w-auto"
              onError={(e) => {
                // Fallback if logo doesn't exist
                e.currentTarget.style.display = 'none'
              }}
            />
          </div>
          <h1 className="text-4xl font-bold mb-2">Welcome to Ollama Chat</h1>
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
          {isLoadingModels && (
            <div className="flex justify-center items-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[hsl(var(--primary))]"></div>
              <span className="ml-2 text-sm text-[hsl(var(--muted-foreground))]">
                Loading available models...
              </span>
            </div>
          )}

          <div className="flex flex-col items-center space-y-3">
            <label className="text-sm text-[hsl(var(--muted-foreground))]">
              Select a model to start chatting
            </label>
            <div className="w-full mx-auto">
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
  )
}

export default WelcomeNote
