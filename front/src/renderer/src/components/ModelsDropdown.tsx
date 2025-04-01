import { ModelOption } from '../fetch/types'
import { getIconPath, getModelDisplayName } from '@renderer/utils'

export const ModelsDropdown = ({
  models,
  selectedModel,
  onChange,
  isLoading,
  disabled
}: {
  models: ModelOption[] | string[]
  selectedModel: string
  onChange: (value: string) => void
  isLoading: boolean
  disabled: boolean
}): JSX.Element => {
  const formattedModels = models.map((model) => {
    if (typeof model === 'string') {
      return { name: model, description: `AI model` }
    }
    return model
  })

  return (
    <div className="relative min-w-[150px] max-w-[300px]">
      <select
        className="w-full p-2 pl-10 border rounded-full bg-[hsl(var(--background))] border-[hsl(var(--input))] appearance-none cursor-pointer overflow-hidden text-ellipsis"
        value={selectedModel}
        onChange={(e) => onChange(e.target.value)}
        disabled={isLoading || disabled}
        title={selectedModel}
      >
        {isLoading ? (
          <option>Loading models...</option>
        ) : formattedModels.length === 0 ? (
          <option>No models available</option>
        ) : (
          formattedModels.map((model) => (
            <option key={model.name} value={model.name} title={model.name}>
              {getModelDisplayName(model.name)}
            </option>
          ))
        )}
      </select>

      {!isLoading && selectedModel && (
        <div className="absolute inset-y-0 left-0 flex items-center pl-2 pointer-events-none">
          <img
            src={getIconPath(selectedModel)}
            alt=""
            className="w-6 h-6 rounded-full"
            onError={(e) => {
              e.currentTarget.src = new URL('../assets/models/default.png', import.meta.url).href
            }}
          />
        </div>
      )}

      <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
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
          <path d="m6 9 6 6 6-6" />
        </svg>
      </div>
    </div>
  )
}
