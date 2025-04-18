import React, { useState, useEffect } from 'react'
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogClose } from '@renderer/components/ui/dialog'
import { Input } from '@renderer/components/ui/input'
import { Button } from '@renderer/components/ui/button'
import { Loader2, Plus } from 'lucide-react'
import { useModels, useModelInfo } from '@renderer/fetch/queries'
import apiClient from '@renderer/fetch/api-client'
import ModelDetailsView from '@renderer/components/ModelDetailsView'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { ModelInfo } from '@renderer/fetch/types'

export default function AddModel() {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [suggestions, setSuggestions] = useState<ModelInfo[]>([])
  const [selectedModel, setSelectedModel] = useState<string | null>(null)

  const { data: modelsRes, isLoading: loadingModels } = useModels(open)

  // filter suggestions when searchTerm changes
  useEffect(() => {
    if (searchTerm.trim() && modelsRes?.models) {
      const matches = modelsRes.models
        .filter(m => m.name.toLowerCase().includes(searchTerm.toLowerCase()))
        .slice(0, 10)
      setSuggestions(matches)
      setSelectedModel(null)
    } else {
      setSuggestions([])
    }
  }, [searchTerm, modelsRes])

  // load details for selectedModel
  const { isLoading: loadingDetails } = useModelInfo(selectedModel)

  // mutation to install model
  const installMutation = useMutation({
    mutationFn: (name: string) => apiClient.post(`/models/${encodeURIComponent(name)}/install`),
    onSuccess: () => {
      // close dialog and refresh models list
      setOpen(false)
      setSearchTerm('')
      setSuggestions([])
      setSelectedModel(null)
      queryClient.invalidateQueries({ queryKey: ['models'] })
    },
  })

  // derive install loading state
  const installing = installMutation.status === 'pending'

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="default"><Plus className="w-4 h-4 mr-2" />Add Model</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add a New Model</DialogTitle>
          <DialogDescription>Search Ollama registry and install a model locally.</DialogDescription>
        </DialogHeader>

        <div className="mt-4 space-y-4">
          <div className="relative">
            <label htmlFor="model-search" className="sr-only">Model name or ID</label>
            <Input
              id="model-search"
              placeholder="Type model name or ID..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              disabled={installing}
            />
            {suggestions.length > 0 && !selectedModel && (
              <ul className="absolute z-10 mt-1 w-full bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded max-h-48 overflow-y-auto">
                {suggestions.map(m => (
                  <li
                    key={m.name}
                    className="px-3 py-2 hover:bg-[hsl(var(--accent))] hover:text-[hsl(var(--accent-foreground))] cursor-pointer"
                    onClick={() => {
                      setSelectedModel(m.name)
                      setSearchTerm(m.name)
                      setSuggestions([])
                    }}
                  >
                    {m.name}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {selectedModel && (
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="font-medium">Preview:</span>
                {loadingDetails && <Loader2 className="h-4 w-4 animate-spin" />}
              </div>
              <ModelDetailsView modelName={selectedModel} />
            </div>
          )}
        </div>

        <DialogFooter>
          <DialogClose asChild>
            <Button variant="secondary" disabled={installing}>Cancel</Button>
          </DialogClose>
          <Button
            onClick={() => selectedModel && installMutation.mutate(selectedModel)}
            disabled={!selectedModel || installing}
          >
            {installing ? (
              <span className="flex items-center">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Installing...
              </span>
            ) : (
              <><Plus className="w-4 h-4 mr-2" />Install Model</>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
