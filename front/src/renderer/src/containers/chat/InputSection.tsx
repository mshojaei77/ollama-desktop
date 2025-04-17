import { Input } from '@renderer/components/ui/input'
import { ModelsDropdown } from '@renderer/components/ModelsDropdown'
import { useChatStore } from '@renderer/store/chatStore'
import { useModels, useSendMessage } from '@renderer/fetch/queries'
import { useState, useRef, useEffect } from 'react'
import { toast } from 'sonner'
import { X, Loader2, Image, Plug, Paperclip } from 'lucide-react'

// Define allowed file types
const ALLOWED_FILE_TYPES = ['.txt', '.md', '.pdf']
const ALLOWED_IMAGE_TYPES = ['.png', '.jpg', '.jpeg', '.webp', '.gif']
const ALL_ALLOWED_TYPES = [...ALLOWED_FILE_TYPES, ...ALLOWED_IMAGE_TYPES]

// Interface for uploaded file info
interface UploadedFile {
  name: string
  id: string
  timestamp: number
}

// Interface for pending image
interface PendingImage {
  name: string
  id: string // Used locally to manage the indicator
}

const InputSection = ({ apiConnected }: { apiConnected: boolean }): JSX.Element => {
  const [input, setInput] = useState('')
  const sessionId = useChatStore((state) => state.sessionId)
  const selectedModel = useChatStore((state) => state.selectedModel)
  const setSelectedModel = useChatStore((state) => state.setSelectedModel)
  const { data: modelsResponse, isLoading: isLoadingModels } = useModels(apiConnected === true)
  const [toolsEnabled, setToolsEnabled] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [pendingImage, setPendingImage] = useState<PendingImage | null>(null)
  const [showTooltip, setShowTooltip] = useState(false)

  const { mutate: sendMessageMutation, isPending: isSending } = useSendMessage()

  // Clear pending image if session changes
  useEffect(() => {
    setPendingImage(null)
    setUploadedFiles([]) // Also clear context files
  }, [sessionId])

  const handleKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const sendMessage = (): void => {
    // Can send message even if only an image is pending and input is empty
    if ((!input.trim() && !pendingImage) || !sessionId) return

    // Input is cleared in the onSuccess callback of the mutation
    // setInput('')

    sendMessageMutation({
      message: input, // Send current text input
      session_id: sessionId
      // The backend implicitly sends the pending image associated with the session
    }, {
      onSuccess: () => {
        // Clear pending image and input after message is successfully sent
        setPendingImage(null)
        setInput('') 
        console.log("Message sent successfully, cleared pending image and input.")
      },
      onError: (error) => {
        // Handle error
        toast.error(`Failed to send message: ${error.message}`)
      }
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

    // Validate file type (allow documents and images)
    if (!ALL_ALLOWED_TYPES.includes(extension)) {
      toast.error(
        `Unsupported file type. Please upload a ${ALLOWED_FILE_TYPES.join(
          ', '
        )} or ${ALLOWED_IMAGE_TYPES.join(', ')} file.`
      )
      return
    }

    // Prevent uploading if an image is already pending
    if (pendingImage && ALLOWED_IMAGE_TYPES.includes(extension)) {
        toast.error("An image is already attached. Send the current message or remove the image first.")
        return
    }

    // Validate file size (limit to 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File too large. Please upload a file smaller than 10MB.')
      return
    }

    try {
      setIsUploading(true)
      
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`http://localhost:8000/sessions/${sessionId}/upload_file`, {
        method: 'POST',
        body: formData
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.detail || 'Error uploading file')
      }

      // Handle response based on type (image or context)
      if (result.type === 'image' && ALLOWED_IMAGE_TYPES.includes(extension)) {
        // Set the pending image state
        setPendingImage({ name: file.name, id: Date.now().toString() })
        toast.success(result.message || `Image "${file.name}" attached. Add a prompt and send.`)
      } else if (result.type === 'context' && ALLOWED_FILE_TYPES.includes(extension)) {
        // Add the file to the uploaded context files list
        const newFile: UploadedFile = {
          name: file.name,
          id: Date.now().toString(), // Simple unique ID
          timestamp: new Date().getTime()
        }
        setUploadedFiles((prev) => [...prev, newFile])
        toast.success(result.message || `File "${file.name}" added to context.`)
      } else {
        // Fallback for unexpected response types or mismatch
        toast.info("File uploaded, but couldn't determine type or type mismatch.")
      }

    } catch (error) {
      toast.error(`Failed to upload file: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  // Remove context file
  const removeContextFile = (id: string) => {
    setUploadedFiles((prev) => prev.filter((file) => file.id !== id))
    toast('Context file removed')
    // TODO: Potentially call backend to remove from vector store if needed?
  }

  // Remove pending image
  const removePendingImage = () => {
    setPendingImage(null)
    toast('Attached image removed')
    // Backend automatically clears image on next send or session cleanup,
    // so no specific backend call needed here just for removing the indicator.
  }

  return (
    <div className="sticky bottom-0 p-4 bg-[hsl(var(--background))]">
      {/* Show uploaded CONTEXT files */} 
      {uploadedFiles.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {uploadedFiles.map((file) => (
            <div
              key={file.id}
              className="flex items-center gap-1.5 bg-blue-100 dark:bg-blue-950 px-2 py-1 rounded-full text-xs"
            >
              <Paperclip size={12} className="text-slate-600 dark:text-slate-400 flex-shrink-0" />
              <span className="truncate max-w-[200px]">{file.name}</span>
              <button
                onClick={() => removeContextFile(file.id)}
                className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex-shrink-0"
                title="Remove context file"
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Show PENDING IMAGE indicator */}
      {pendingImage && (
          <div className="mb-2 flex flex-wrap gap-2">
              <div
                key={pendingImage.id}
                className="flex items-center gap-1.5 bg-green-100 dark:bg-green-950 px-2 py-1 rounded-full text-xs"
              >
                <Image size={12} className="text-green-700 dark:text-green-300 flex-shrink-0" />
                <span className="truncate max-w-[200px]">{pendingImage.name}</span>
                <button
                    onClick={removePendingImage}
                    className="text-green-700 dark:text-green-300 hover:text-slate-900 dark:hover:text-white flex-shrink-0"
                    title="Remove attached image"
                >
                    <X size={14} />
                </button>
              </div>
          </div>
      )}

      <div className="flex flex-col w-full bg-[hsl(var(--card))] rounded-lg border">
        <div className="px-4 pt-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={pendingImage ? "Add a prompt for the image..." : "Ask anything"}
            disabled={isSending}
            className="border-none focus:border-none focus-visible:ring-0 focus-visible:ring-offset-0 bg-transparent w-full text-sm px-0 placeholder-[hsl(var(--muted-foreground))]"
          />
        </div>
        
        <div className="flex items-center gap-2 mt-1 pb-3">
          <div className="pl-4">
            <ModelsDropdown
              models={modelsResponse?.models || []}
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
              <Plug size={18} />
            </button>

            {/* File upload input (unified for both types) */}
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileUpload} 
              className="hidden" 
              accept={ALL_ALLOWED_TYPES.join(',')}
            />
             {/* Attachment Button (Context Files) */}
            <button 
              onClick={handleAttachmentClick}
              disabled={isUploading || !sessionId || !apiConnected}
              className="p-1.5 text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] disabled:opacity-50 relative"
              title={`Upload context file (${ALLOWED_FILE_TYPES.join(', ')})`}
            >
              {isUploading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Paperclip size={18} />
              )}
            </button>

            {/* Image Upload Button */}
            <button
              onClick={handleAttachmentClick}
              disabled={isUploading || !!pendingImage || !sessionId || !apiConnected} // Disable if uploading or image pending
              className="p-1.5 text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] disabled:opacity-50"
              title={pendingImage ? "Image already attached" : `Upload an image (${ALLOWED_IMAGE_TYPES.join(', ')})`}
            >
              {isUploading ? (
                 <Loader2 size={18} className="animate-spin" />
               ) : (
                <Image size={18} />
               )}
            </button>

            <button
              onClick={sendMessage}
              disabled={isSending || (!input.trim() && !pendingImage) || !sessionId} // Allow sending if image is pending
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
