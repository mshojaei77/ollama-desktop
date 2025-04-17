import React, { useState } from 'react'
import { useModels, useModelInfo } from './fetch/queries'
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card'
import { Loader2 } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose
} from './components/ui/dialog'
import { Button } from './components/ui/button'
import ModelDetailsView from './components/ModelDetailsView'

const Models: React.FC = () => {
  const { data: modelsResponse, isLoading: isLoadingModels, error: modelsError, isError: isModelsError } = useModels()
  const [selectedModelName, setSelectedModelName] = useState<string | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  const handleModelClick = (modelName: string) => {
    setSelectedModelName(modelName)
    setIsDialogOpen(true)
  }

  return (
    <div className="flex flex-col h-full p-4 space-y-4 bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
      <h1 className="text-2xl font-semibold">Available Ollama Models</h1>
      <Card className="flex-grow flex flex-col border-[hsl(var(--border))] bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))]">
        <CardHeader className="border-b border-[hsl(var(--border))]">
          <CardTitle>Installed Models</CardTitle>
        </CardHeader>
        <CardContent className="p-4 flex-grow overflow-y-auto">
          {isLoadingModels && (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-8 w-8 animate-spin text-[hsl(var(--primary))]" />
              <span className="ml-2">Loading models...</span>
            </div>
          )}
          {isModelsError && (
            <div className="text-center text-red-600">
              Failed to fetch models: {modelsError instanceof Error ? modelsError.message : 'Unknown error'}
            </div>
          )}
          {!isLoadingModels && !isModelsError && (
            <ul className="list-none pl-0">
              {modelsResponse?.models && modelsResponse.models.length > 0 ? (
                modelsResponse.models.map((model) => (
                  <Dialog key={model.name} open={isDialogOpen && selectedModelName === model.name} onOpenChange={(open) => { if (!open) { setIsDialogOpen(false); setSelectedModelName(null); } else { setIsDialogOpen(open); setSelectedModelName(model.name); } }}>
                    <DialogTrigger asChild>
                      <li 
                        className="py-2 px-3 cursor-pointer hover:bg-[hsl(var(--muted)/50%)] rounded transition-colors duration-150 border-b border-[hsl(var(--border))] last:border-b-0"
                        onClick={() => handleModelClick(model.name)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => e.key === 'Enter' && handleModelClick(model.name)}
                      >
                        {model.name}
                      </li>
                    </DialogTrigger>
                    {selectedModelName === model.name && (
                      <DialogContent className="sm:max-w-[600px]">
                        <DialogHeader>
                          <DialogTitle>Model Details: {model.name}</DialogTitle>
                          <DialogDescription>
                            Detailed information retrieved from Ollama.
                          </DialogDescription>
                        </DialogHeader>
                        <ModelDetailsView modelName={selectedModelName} />
                        <DialogFooter>
                          <DialogClose asChild>
                            <Button type="button" variant="secondary">
                              Close
                            </Button>
                          </DialogClose>
                        </DialogFooter>
                      </DialogContent>
                    )}
                  </Dialog>
                ))
              ) : (
                <li className="text-center text-[hsl(var(--muted-foreground))] py-4">No models found.</li>
              )}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default Models
