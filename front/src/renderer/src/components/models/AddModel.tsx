import React, { useState, useEffect } from 'react'
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogClose } from '@renderer/components/ui/dialog'
import { Input } from '@renderer/components/ui/input'
import { Button } from '@renderer/components/ui/button'
import { Loader2, Plus, Check } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import apiClient from '@renderer/fetch/api-client'
import type { ModelInfo } from '@renderer/fetch/types'

// Type for scraped model item (with extra fields)
interface ScrapedModel {
  name: string
  info: string
  tags: string[]
  sizes: string[]
}

// Type for scraped models response
interface ScrapedModelsResponse {
  popular: ScrapedModel[]
  vision: ScrapedModel[]
  tools: ScrapedModel[]
  newest: ScrapedModel[]
}

export default function AddModel() {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [suggestions, setSuggestions] = useState<ScrapedModel[]>([])
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [pulling, setPulling] = useState(false)
  const [progress, setProgress] = useState<Record<string, { completed: number; total: number; status?: string }>>({})

  // Scraped models list
  const [scrapedModels, setScrapedModels] = useState<ScrapedModel[]>([])

  // Compute model for preview and find scraped details if available
  const modelToPreview = selectedModel || searchTerm
  const scrapedInfo = scrapedModels.find(m => m.name === modelToPreview)

  // Fetch scraped models when dialog opens
  useEffect(() => {
    if (open) {
      apiClient.get<ScrapedModelsResponse>('/models/scraped')
        .then(({ data }) => {
          const merged = [
            ...data.popular,
            ...data.vision,
            ...data.tools,
            ...data.newest
          ]
          // Deduplicate by name
          const uniqueModels = Array.from(
            new Map(merged.map(m => [m.name, m])).values()
          )
          setScrapedModels(uniqueModels)
        })
        .catch(console.error)
    }
  }, [open])

  // Filter scraped models suggestions based on searchTerm
  useEffect(() => {
    if (searchTerm.trim() && scrapedModels.length) {
      const matches = scrapedModels
        .filter(m => m.name.toLowerCase().includes(searchTerm.toLowerCase()))
        .slice(0, 10)
      setSuggestions(matches)
      setSelectedModel(null)
    } else {
      setSuggestions([])
    }
  }, [searchTerm, scrapedModels])

  // Function to handle model pull with streaming progress
  async function handlePull() {
    const modelToPull = selectedModel || searchTerm
    if (!modelToPull) return
    setPulling(true)
    setProgress({})
    try {
      // Use full API URL to avoid same-origin issues
      const base = (apiClient.defaults.baseURL || '').replace(/\/$/, '')
      const apiUrl = `${base}/models/${encodeURIComponent(modelToPull)}/pull?stream=true`
      const response = await fetch(apiUrl)
      if (!response.ok) {
        alert(`Failed to start download: ${response.statusText}`)
        return
      }
      if (!response.body) {
        alert('No response body for streaming')
        return
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (!line) continue
          try {
            const prog = JSON.parse(line)
            setProgress(prev => ({
              ...prev,
              [prog.digest || prog.status || Math.random().toString()]: {
                completed: prog.completed || 0,
                total: prog.total || 0,
                status: prog.status
              }
            }))
          } catch {}
        }
      }
      // On completion, optionally refresh installed models list
      queryClient.invalidateQueries({ queryKey: ['models'] })
    } catch (error) {
      console.error(error)
      alert(`Download error: ${error}`)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="default"><Plus className="w-4 h-4 mr-2" />Add Model</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        {/* Render UI based on pulling state */}
        {pulling ? (
          <div className="space-y-4 text-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto" />
            <div className="font-semibold">Downloading model {modelToPreview}...</div>
            {Object.entries(progress).map(([key, { completed, total, status }]) => (
              <div key={key} className="space-y-1">
                {status && (
                  <div className="flex items-center justify-center text-sm text-gray-600">
                    {status === 'success' && <Check className="h-4 w-4 text-green-500 mr-2" />}
                    <span>{status}</span>
                  </div>
                )}
                {total > 0 && (
                  <progress value={completed} max={total} className="w-full h-2">
                    {Math.round((completed / total) * 100)}%
                  </progress>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            <DialogHeader>
              <DialogTitle>Add a New Model</DialogTitle>
              <DialogDescription>Type or select a Model ID to install.</DialogDescription>
            </DialogHeader>
            <div className="mt-4 space-y-4">
              <div className="relative">
                <label htmlFor="model-search" className="sr-only">Model ID to install</label>
                <Input
                  id="model-search"
                  placeholder="Type model ID to install..."
                  value={searchTerm}
                  onChange={e => setSearchTerm(e.target.value)}
                  disabled={false}
                />
                {suggestions.length > 0 && (
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
              {modelToPreview && scrapedInfo && (
                <div className="space-y-2">
                  <div className="font-medium">Preview:</div>
                  <p className="text-sm text-gray-700">{scrapedInfo.info}</p>
                  {scrapedInfo.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {scrapedInfo.tags.map(tag => (
                        <span key={tag} className="px-2 py-1 bg-gray-200 rounded text-xs">{tag}</span>
                      ))}
                    </div>
                  )}
                  {scrapedInfo.sizes.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {scrapedInfo.sizes.map(size => (
                        <span key={size} className="px-2 py-1 bg-blue-100 rounded text-xs">{size}</span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        <DialogFooter>
          {!pulling ? (
            <>
              <DialogClose asChild>
                <Button variant="secondary">Cancel</Button>
              </DialogClose>
              <Button onClick={handlePull} disabled={!searchTerm.trim()}>
                <Plus className="w-4 h-4 mr-2" />Install Model
              </Button>
            </>
          ) : (
            <DialogClose asChild>
              <Button variant="default" onClick={() => setPulling(false)}>Close</Button>
            </DialogClose>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
