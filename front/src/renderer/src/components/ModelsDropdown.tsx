import { ModelOption } from '../fetch/types'
import { getIconPath, getModelDisplayName } from '@renderer/utils'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { useEffect } from 'react'

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

  // Auto-select first model if none is selected and models are available
  useEffect(() => {
    if (!isLoading && formattedModels.length > 0 && !selectedModel) {
      onChange(formattedModels[0].name)
    }
  }, [isLoading, formattedModels, selectedModel, onChange])

  // Use the first model's value as default if no value is selected
  const selectValue = selectedModel || (formattedModels.length > 0 ? formattedModels[0].name : '')

  return (
    <div className="relative min-w-[150px] max-w-[300px] mx-auto">
      <Select value={selectValue} onValueChange={onChange} disabled={isLoading || disabled}>
        <SelectTrigger className="w-full rounded-xl text-[hsl(var(--foreground))]">
          <div className="flex items-center gap-2">
            {!isLoading && selectValue && (
              <img
                src={getIconPath(selectValue)}
                alt=""
                className="w-6 h-6 rounded-full"
                onError={(e) => {
                  e.currentTarget.src = new URL('../assets/models/default.png', import.meta.url).href
                }}
              />
            )}
            {!isLoading && selectValue ? (
              <span className="flex-1 text-left truncate">
                {getModelDisplayName(selectValue)}
              </span>
            ) : (
              <SelectValue placeholder={isLoading ? 'Loading models...' : 'Select model'} />
            )}
          </div>
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
    </div>
  )
}
