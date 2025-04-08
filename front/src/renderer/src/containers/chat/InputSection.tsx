import { Input } from '@renderer/components/ui/input'
import { ModelsDropdown } from '@renderer/components/ModelsDropdown'
import { useChatStore } from '@renderer/store/chatStore'
import { useModels, useSendMessage } from '@renderer/fetch/queries'
import { useState, useRef } from 'react'
import { toast } from 'sonner'
import { X, Loader2 } from 'lucide-react'

// Define allowed file types
const ALLOWED_FILE_TYPES = ['.txt', '.md', '.pdf']

// Interface for uploaded file info
interface UploadedFile {
  name: string
  id: string
  timestamp: number
}

const InputSection = ({ apiConnected }: { apiConnected: boolean }): JSX.Element => {
  const [input, setInput] = useState('')
  const sessionId = useChatStore((state) => state.sessionId)
  const selectedModel = useChatStore((state) => state.selectedModel)
  const setSelectedModel = useChatStore((state) => state.setSelectedModel)
  const { data: models = [], isLoading: isLoadingModels } = useModels(apiConnected === true)
  const [toolsEnabled, setToolsEnabled] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [showTooltip, setShowTooltip] = useState(false)

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
      session_id: sessionId
    })
  }

  const handleAttachmentClick = () => {
    // Trigger the hidden file input click
    fileInputRef.current?.click()
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || !files.length || !sessionId) return

    const file = files[0]
    const extension = '.' + file.name.split('.').pop()?.toLowerCase()

    // Validate file type
    if (!ALLOWED_FILE_TYPES.includes(extension)) {
      toast.error(`Unsupported file type. Please upload a ${ALLOWED_FILE_TYPES.join(', ')} file.`)
      return
    }

    // Validate file size (limit to 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File too large. Please upload a file smaller than 10MB.')
      return
    }

    try {
      setIsUploading(true)
      
      // Create form data
      const formData = new FormData()
      formData.append('file', file)

      // Upload the file
      const response = await fetch(`http://localhost:8000/sessions/${sessionId}/upload_file`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Error uploading file' }))
        throw new Error(errorData.detail || 'Error uploading file')
      }

      // Add the file to the uploaded files list
      const newFile: UploadedFile = {
        name: file.name,
        id: new Date().getTime().toString(),
        timestamp: new Date().getTime()
      }
      
      setUploadedFiles(prev => [...prev, newFile])
      toast.success(`File "${file.name}" uploaded successfully.`)
    } catch (error) {
      toast.error(`Failed to upload file: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsUploading(false)
      // Reset the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const removeFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== id))
    toast('File removed from context')
  }

  return (
    <div className="sticky bottom-0 p-4 bg-[hsl(var(--background))]">
      {/* Show uploaded files that serve as context */}
      {uploadedFiles.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {uploadedFiles.map(file => (
            <div 
              key={file.id}
              className="flex items-center gap-1.5 bg-blue-100 dark:bg-blue-950 px-2 py-1 rounded-full text-xs"
            >
              <span className="truncate max-w-[200px]">{file.name}</span>
              <button 
                onClick={() => removeFile(file.id)}
                className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-col w-full bg-[hsl(var(--card))] rounded-2xl py-3 border border-[hsl(var(--border))] shadow-sm">
        <div className="px-4">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything"
            disabled={isSending}
            className="border-0 focus-visible:ring-0 focus-visible:ring-offset-0 bg-transparent w-full text-sm px-0 placeholder-[hsl(var(--muted-foreground))]"
          />
        </div>
        
        <div className="flex items-center gap-2 mt-1">
          <div className="pl-2">
            <ModelsDropdown
              models={models}
              selectedModel={selectedModel}
              onChange={(value) => setSelectedModel(value)}
              isLoading={isLoadingModels}
              disabled={apiConnected !== true}
            />
          </div>

          <div className="flex items-center gap-2 ml-auto pr-4">
            <button 
              onClick={() => setToolsEnabled(!toolsEnabled)}
              className={`p-1.5 ${toolsEnabled ? 'text-blue-600' : 'text-[hsl(var(--muted-foreground))]'} hover:text-[hsl(var(--foreground))]`}
              title={toolsEnabled ? "Disable tools" : "Enable tools"}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
              </svg>
            </button>

            {/* File upload input and button */}
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileUpload} 
              className="hidden" 
              accept=".txt,.md,.pdf"
            />
            <div 
              className="relative"
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
            >
              <button 
                onClick={handleAttachmentClick}
                disabled={isUploading || !sessionId || !apiConnected}
                className="p-1.5 text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] disabled:opacity-50 relative"
                title="Upload a file as context (.txt, .md, .pdf)"
              >
                {isUploading ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
                  </svg>
                )}
              </button>
              {showTooltip && (
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded shadow-lg whitespace-nowrap z-50">
                  Upload a file as context (.txt, .md, .pdf)
                </div>
              )}
            </div>

            <button
              onClick={sendMessage}
              disabled={isSending || !input.trim()}
              className="p-1.5 text-blue-600 hover:text-blue-700 disabled:opacity-50"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
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
    </div>
  )
}

export default InputSection
