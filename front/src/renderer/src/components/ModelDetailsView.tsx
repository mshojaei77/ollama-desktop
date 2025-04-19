import React from 'react'
import ollamaModelsData from '../assets/ollama_models.json'
import { useModelInfo } from '@renderer/fetch/queries' // Use alias path
import { Loader2 } from 'lucide-react'

// Helper component to display model details in the dialog
const ModelDetailsView: React.FC<{ modelName: string }> = ({ modelName }) => {
  const { data: details, isLoading, isError, error } = useModelInfo(modelName)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <Loader2 className="h-6 w-6 animate-spin text-[hsl(var(--primary))]" />
        <span className="ml-2">Loading details...</span>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="text-center text-red-600 min-h-[200px] flex items-center justify-center">
        Failed to load details: {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    )
  }

  if (!details) {
    return <div className="text-center min-h-[200px] flex items-center justify-center">No details available.</div>
  }

  // Filter out internal/unwanted keys and format the display
  const displayableDetails = Object.entries(details)
    .filter(([key]) => !['model_name', 'type'].includes(key)) // Example: exclude some keys
    .sort(([keyA], [keyB]) => keyA.localeCompare(keyB)); // Sort alphabetically

  // Lookup JSON entry for this model (exact or prefix match)
  const jsonEntry = ollamaModelsData.popular.find(item =>
    item.name.toLowerCase() === modelName.toLowerCase() ||
    modelName.toLowerCase().startsWith(item.name.toLowerCase())
  )

  return (
    <div className="space-y-3 text-sm max-h-[60vh] overflow-y-auto pr-2">
      {jsonEntry?.info && (
        <div className="font-medium text-sm mb-1">{jsonEntry.info}</div>
      )}
      {jsonEntry?.tags?.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {jsonEntry.tags.map(tag => (
            <span key={tag} className="px-2 py-1 bg-gray-200 rounded text-xs">{tag}</span>
          ))}
        </div>
      )}
      {displayableDetails.map(([key, value]) => (
        <div key={key} className="flex justify-between border-b pb-1 border-[hsl(var(--border))]">
          <span className="font-medium capitalize text-[hsl(var(--muted-foreground))]">
            {key.replace(/_/g, ' ')}:
          </span>
          <span className="text-right break-all">
            {Array.isArray(value)
              ? value.join(', ')
              : typeof value === 'number'
                ? value.toLocaleString() // Format numbers
                : String(value)}
          </span>
        </div>
      ))}
    </div>
  )
}

export default ModelDetailsView 