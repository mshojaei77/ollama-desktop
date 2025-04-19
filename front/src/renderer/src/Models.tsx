import React, { useState, useEffect, useMemo } from 'react'
import { useModels } from './fetch/queries'
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
import {
  MessageSquare,
  Image,
  Hash,
  ArrowUpDown,
  Search,
  Database,
  Info,
  ExternalLink,
  RefreshCw
} from 'lucide-react'
import ModelDetailsView from './components/ModelDetailsView'
import apiClient from './fetch/api-client'
import { ModelDetails } from './fetch/types'
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from './components/ui/select'
import { getIconPath, getModelDisplayName } from './utils'
import embedIcon from './assets/models/embed.png'
import AddModel from './components/models/AddModel'

const Models: React.FC = () => {
  const { data: modelsResponse, isLoading: isLoadingModels, error: modelsError, isError: isModelsError, refetch: refetchModels } = useModels()
  const [selectedModelName, setSelectedModelName] = useState<string | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  type SortOption = 'default' | 'nameAsc' | 'nameDesc' | 'paramAsc' | 'paramDesc'
  const [textSortOption, setTextSortOption] = useState<SortOption>('default')
  const [visionSortOption, setVisionSortOption] = useState<SortOption>('default')
  const [embedSortOption, setEmbedSortOption] = useState<SortOption>('default')
  const [modelInfos, setModelInfos] = useState<Record<string, ModelDetails>>(() => {
    const cached = localStorage.getItem('modelInfos')
    return cached ? JSON.parse(cached) : {}
  })

  // Fetch model details once per model for caching
  useEffect(() => {
    const fetchInfos = async () => {
      if (!modelsResponse?.models) return
      for (const { name } of modelsResponse.models) {
        if (!modelInfos[name]) {
          try {
            const { data } = await apiClient.get<ModelDetails>(
              `/models/${encodeURIComponent(name)}/info`
            )
            setModelInfos(prev => {
              const updated = { ...prev, [name]: data }
              try {
                localStorage.setItem('modelInfos', JSON.stringify(updated))
              } catch (e) {
                console.error('Failed to cache model infos', e)
              }
              return updated
            })
          } catch (error) {
            console.error('Failed to fetch model info for', name, error)
          }
        }
      }
    }
    fetchInfos()
  }, [modelsResponse])

  // Utility to parse sizes like '7B', '2.7B'
  const parseParamSize = (size?: string): number => {
    const s = (size || '').trim().toUpperCase()
    const match = s.match(/^([\d\.]+)\s*([KMBT]?)(B?)$/)
    if (!match) return 0
    const num = parseFloat(match[1])
    const unit = match[2]
    const mul = unit === 'K' ? 1e3 : unit === 'M' ? 1e6 : unit === 'B' ? 1e9 : unit === 'T' ? 1e12 : 1
    return num * mul
  }

  const handleModelClick = (modelName: string) => {
    setSelectedModelName(modelName)
    setIsDialogOpen(true)
  }

  // Categorize models into three groups based on name patterns and family
  const multimodalPatterns = ['vision', 'clip', 'image']
  const textGenerationModels = modelsResponse?.models.filter((m) => {
    const nameLower = m.name.toLowerCase()
    const isVision = multimodalPatterns.some((p) => nameLower.includes(p))
    const isEmbedName = nameLower.includes('embed')
    const isBertFamily = modelInfos[m.name]?.family?.toLowerCase() === 'bert'
    return !isVision && !isEmbedName && !isBertFamily
  }) || []
  const multimodalModels = modelsResponse?.models.filter((m) => {
    const nameLower = m.name.toLowerCase()
    const isVision = multimodalPatterns.some((p) => nameLower.includes(p))
    const isBertFamily = modelInfos[m.name]?.family?.toLowerCase() === 'bert'
    return isVision && !isBertFamily
  }) || []
  const embeddingModels = modelsResponse?.models.filter((m) => {
    const nameLower = m.name.toLowerCase()
    const isEmbedName = nameLower.includes('embed')
    const isBertFamily = modelInfos[m.name]?.family?.toLowerCase() === 'bert'
    return isEmbedName || isBertFamily
  }) || []

  // Prepare sorted lists and choose display based on sortOrder
  const sortedTextAsc = [...textGenerationModels].sort((a, b) => a.name.localeCompare(b.name))
  const sortedTextDesc = [...textGenerationModels].sort((a, b) => b.name.localeCompare(a.name))
  const displayedTextGenerationModels = useMemo(() => {
    switch (textSortOption) {
      case 'nameAsc': return [...textGenerationModels].sort((a, b) => a.name.localeCompare(b.name))
      case 'nameDesc': return [...textGenerationModels].sort((a, b) => b.name.localeCompare(a.name))
      case 'paramAsc': return [...textGenerationModels].sort((a, b) => parseParamSize(modelInfos[a.name]?.parameter_size) - parseParamSize(modelInfos[b.name]?.parameter_size))
      case 'paramDesc': return [...textGenerationModels].sort((a, b) => parseParamSize(modelInfos[b.name]?.parameter_size) - parseParamSize(modelInfos[a.name]?.parameter_size))
      default: return textGenerationModels
    }
  }, [textGenerationModels, textSortOption, modelInfos])

  const sortedVisionAsc = [...multimodalModels].sort((a, b) => a.name.localeCompare(b.name))
  const sortedVisionDesc = [...multimodalModels].sort((a, b) => b.name.localeCompare(a.name))
  const displayedVisionModels = useMemo(() => {
    switch (visionSortOption) {
      case 'nameAsc': return [...multimodalModels].sort((a, b) => a.name.localeCompare(b.name))
      case 'nameDesc': return [...multimodalModels].sort((a, b) => b.name.localeCompare(a.name))
      case 'paramAsc': return [...multimodalModels].sort((a, b) => parseParamSize(modelInfos[a.name]?.parameter_size) - parseParamSize(modelInfos[b.name]?.parameter_size))
      case 'paramDesc': return [...multimodalModels].sort((a, b) => parseParamSize(modelInfos[b.name]?.parameter_size) - parseParamSize(modelInfos[a.name]?.parameter_size))
      default: return multimodalModels
    }
  }, [multimodalModels, visionSortOption, modelInfos])

  const sortedEmbedAsc = [...embeddingModels].sort((a, b) => a.name.localeCompare(b.name))
  const sortedEmbedDesc = [...embeddingModels].sort((a, b) => b.name.localeCompare(a.name))
  const displayedEmbeddingModels = useMemo(() => {
    switch (embedSortOption) {
      case 'nameAsc': return [...embeddingModels].sort((a, b) => a.name.localeCompare(b.name))
      case 'nameDesc': return [...embeddingModels].sort((a, b) => b.name.localeCompare(a.name))
      case 'paramAsc': return [...embeddingModels].sort((a, b) => parseParamSize(modelInfos[a.name]?.parameter_size) - parseParamSize(modelInfos[b.name]?.parameter_size))
      case 'paramDesc': return [...embeddingModels].sort((a, b) => parseParamSize(modelInfos[b.name]?.parameter_size) - parseParamSize(modelInfos[a.name]?.parameter_size))
      default: return embeddingModels
    }
  }, [embeddingModels, embedSortOption, modelInfos])

  return (
    <div className="container mx-auto px-6 py-8 bg-[hsl(var(--background))] text-[hsl(var(--foreground))] min-h-screen">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Model Library</h1>
          <p className="text-base text-[hsl(var(--muted-foreground))] mt-1">Browse and manage your Ollama models</p>
        </div>
        <div className="flex items-center space-x-2 mt-4 sm:mt-0">
          <Button variant="outline" onClick={() => window.open('https://ollama.com/search', '_blank')}>
            <ExternalLink className="w-4 h-4 mr-2" />Browse Models
          </Button>
          <AddModel />
          <Button variant="outline" onClick={() => { localStorage.removeItem('modelsResponse'); refetchModels(); }}>
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>
      <div className="space-y-12">
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
          <>
            {/* Text Generation Models */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="flex items-center text-lg font-medium uppercase tracking-wide">
                <MessageSquare className="w-5 h-5 mr-2 text-[hsl(var(--primary))]" />
                Text Generation
              </h2>
              <div className="flex items-center space-x-2">
                <Select value={textSortOption} onValueChange={(v) => setTextSortOption(v as SortOption)}>
                  <SelectTrigger className="w-32 px-2 py-1 rounded-lg text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] focus:ring-0 focus:ring-offset-0 border-none">
                    <ArrowUpDown className="w-3 h-3 mr-1 inline-block" />
                    <SelectValue placeholder="Sort" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="default">Default</SelectItem>
                    <SelectItem value="nameAsc">Name A → Z</SelectItem>
                    <SelectItem value="nameDesc">Name Z → A</SelectItem>
                    <SelectItem value="paramAsc">Param Size ↑</SelectItem>
                    <SelectItem value="paramDesc">Param Size ↓</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid gap-8" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
              {displayedTextGenerationModels.map((model) => (
                <Dialog key={model.name} open={isDialogOpen && selectedModelName === model.name} onOpenChange={(open) => { if (!open) { setIsDialogOpen(false); setSelectedModelName(null); } else { setIsDialogOpen(open); setSelectedModelName(model.name); } }}>
                  <DialogTrigger asChild>
                    <div className="group relative p-4 bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))] rounded-xl shadow-md hover:shadow-lg cursor-pointer flex flex-col items-center transition transform hover:scale-105" onClick={() => handleModelClick(model.name)}>
                      <Info className="absolute top-2 right-2 w-4 h-4 text-[hsl(var(--muted-foreground))] opacity-0 group-hover:opacity-100 transition" />
                      <img src={modelInfos[model.name]?.family?.toLowerCase() === 'bert' ? embedIcon : getIconPath(model.name)} alt={model.name} className="w-10 h-10 mb-1" />
                      <span className="font-medium truncate">{getModelDisplayName(model.name)}</span>
                      <div className="flex items-center text-sm text-[hsl(var(--muted-foreground))] mt-1">
                        <Database className="w-4 h-4 mr-1" />
                        <span>{modelInfos[model.name]?.parameter_size || '—'}</span>
                      </div>
                    </div>
                  </DialogTrigger>
                  {selectedModelName === model.name && (
                    <DialogContent className="sm:max-w-[600px]">
                      <DialogHeader>
                        <DialogTitle>Model Details: {model.name}</DialogTitle>
                        <DialogDescription>Detailed information retrieved from Ollama.</DialogDescription>
                      </DialogHeader>
                      <ModelDetailsView modelName={selectedModelName} />
                      <DialogFooter>
                        <DialogClose asChild><Button type="button" variant="secondary">Close</Button></DialogClose>
                      </DialogFooter>
                    </DialogContent>
                  )}
                </Dialog>
              ))}
              {displayedTextGenerationModels.length === 0 && <div className="col-span-full text-center text-[hsl(var(--muted-foreground))] py-4">No text generation models found.</div>}
            </div>

            {/* Vision Models */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="flex items-center text-lg font-medium uppercase tracking-wide">
                <Image className="w-5 h-5 mr-2 text-[hsl(var(--primary))]" />
                Vision
              </h2>
              <div className="flex items-center space-x-2">
                <Select value={visionSortOption} onValueChange={(v) => setVisionSortOption(v as SortOption)}>
                  <SelectTrigger className="w-32 px-2 py-1 rounded-lg text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] focus:ring-0 focus:ring-offset-0 border-none">
                    <ArrowUpDown className="w-3 h-3 mr-1 inline-block" />
                    <SelectValue placeholder="Sort" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="default">Default</SelectItem>
                    <SelectItem value="nameAsc">Name A → Z</SelectItem>
                    <SelectItem value="nameDesc">Name Z → A</SelectItem>
                    <SelectItem value="paramAsc">Param Size ↑</SelectItem>
                    <SelectItem value="paramDesc">Param Size ↓</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid gap-8" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
              {displayedVisionModels.map((model) => (
                <Dialog key={model.name} open={isDialogOpen && selectedModelName === model.name} onOpenChange={(open) => { if (!open) { setIsDialogOpen(false); setSelectedModelName(null); } else { setIsDialogOpen(open); setSelectedModelName(model.name); } }}>
                  <DialogTrigger asChild>
                    <div className="group relative p-4 bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))] rounded-xl shadow-md hover:shadow-lg cursor-pointer flex flex-col items-center transition transform hover:scale-105" onClick={() => handleModelClick(model.name)}>
                      <Info className="absolute top-2 right-2 w-4 h-4 text-[hsl(var(--muted-foreground))] opacity-0 group-hover:opacity-100 transition" />
                      <img src={modelInfos[model.name]?.family?.toLowerCase() === 'bert' ? embedIcon : getIconPath(model.name)} alt={model.name} className="w-10 h-10 mb-1" />
                      <span className="font-medium truncate">{getModelDisplayName(model.name)}</span>
                      <div className="flex items-center text-sm text-[hsl(var(--muted-foreground))] mt-1">
                        <Database className="w-4 h-4 mr-1" />
                        <span>{modelInfos[model.name]?.parameter_size || '—'}</span>
                      </div>
                    </div>
                  </DialogTrigger>
                  {selectedModelName === model.name && (
                    <DialogContent className="sm:max-w-[600px]">
                      <DialogHeader>
                        <DialogTitle>Model Details: {model.name}</DialogTitle>
                        <DialogDescription>Detailed information retrieved from Ollama.</DialogDescription>
                      </DialogHeader>
                      <ModelDetailsView modelName={selectedModelName} />
                      <DialogFooter>
                        <DialogClose asChild><Button type="button" variant="secondary">Close</Button></DialogClose>
                      </DialogFooter>
                    </DialogContent>
                  )}
                </Dialog>
              ))}
              {displayedVisionModels.length === 0 && <div className="col-span-full text-center text-[hsl(var(--muted-foreground))] py-4">No vision models found.</div>}
            </div>

            {/* Embedding Models */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="flex items-center text-lg font-medium uppercase tracking-wide">
                <Hash className="w-5 h-5 mr-2 text-[hsl(var(--primary))]" />
                Embedding
              </h2>
              <div className="flex items-center space-x-2">
                <Select value={embedSortOption} onValueChange={(v) => setEmbedSortOption(v as SortOption)}>
                  <SelectTrigger className="w-32 px-2 py-1 rounded-lg text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] focus:ring-0 focus:ring-offset-0 border-none">
                    <ArrowUpDown className="w-3 h-3 mr-1 inline-block" />
                    <SelectValue placeholder="Sort" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="default">Default</SelectItem>
                    <SelectItem value="nameAsc">Name A → Z</SelectItem>
                    <SelectItem value="nameDesc">Name Z → A</SelectItem>
                    <SelectItem value="paramAsc">Param Size ↑</SelectItem>
                    <SelectItem value="paramDesc">Param Size ↓</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid gap-8" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
              {displayedEmbeddingModels.map((model) => (
                <Dialog key={model.name} open={isDialogOpen && selectedModelName === model.name} onOpenChange={(open) => { if (!open) { setIsDialogOpen(false); setSelectedModelName(null); } else { setIsDialogOpen(open); setSelectedModelName(model.name); } }}>
                  <DialogTrigger asChild>
                    <div className="group relative p-4 bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))] rounded-xl shadow-md hover:shadow-lg cursor-pointer flex flex-col items-center transition transform hover:scale-105" onClick={() => handleModelClick(model.name)}>
                      <Info className="absolute top-2 right-2 w-4 h-4 text-[hsl(var(--muted-foreground))] opacity-0 group-hover:opacity-100 transition" />
                      <img src={modelInfos[model.name]?.family?.toLowerCase() === 'bert' ? embedIcon : getIconPath(model.name)} alt={model.name} className="w-10 h-10 mb-1" />
                      <span className="font-medium truncate">{getModelDisplayName(model.name)}</span>
                      <div className="flex items-center text-sm text-[hsl(var(--muted-foreground))] mt-1">
                        <Database className="w-4 h-4 mr-1" />
                        <span>{modelInfos[model.name]?.parameter_size || '—'}</span>
                      </div>
                    </div>
                  </DialogTrigger>
                  {selectedModelName === model.name && (
                    <DialogContent className="sm:max-w-[600px]">
                      <DialogHeader>
                        <DialogTitle>Model Details: {model.name}</DialogTitle>
                        <DialogDescription>Detailed information retrieved from Ollama.</DialogDescription>
                      </DialogHeader>
                      <ModelDetailsView modelName={selectedModelName} />
                      <DialogFooter>
                        <DialogClose asChild><Button type="button" variant="secondary">Close</Button></DialogClose>
                      </DialogFooter>
                    </DialogContent>
                  )}
                </Dialog>
              ))}
              {displayedEmbeddingModels.length === 0 && <div className="col-span-full text-center text-[hsl(var(--muted-foreground))] py-4">No embedding models found.</div>}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default Models
