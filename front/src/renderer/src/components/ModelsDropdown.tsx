import { ModelOption } from '../fetch/types'
import { getIconPath, getModelDisplayName } from '@renderer/utils'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'

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
    <div className="relative min-w-[150px] max-w-[300px] mx-auto">
      <Select value={selectedModel} onValueChange={onChange} disabled={isLoading || disabled}>
        <SelectTrigger className="w-full pl-10 rounded-xl ">
          <SelectValue placeholder={isLoading ? 'Loading models...' : 'Select model'} />
        </SelectTrigger>

        <SelectContent className="max-h-60 overflow-y-auto min-w-[150px] max-w-[300px]">
          {isLoading ? (
            <SelectItem value="loading" disabled>
              Loading models...
            </SelectItem>
          ) : formattedModels.length === 0 ? (
            <SelectItem value="none" disabled>
              No models available
            </SelectItem>
          ) : (
            formattedModels.map((model) => (
              <SelectItem key={model.name} value={model.name}>
                {getModelDisplayName(model.name)}
              </SelectItem>
            ))
          )}
        </SelectContent>
      </Select>

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
    </div>
  )
}
