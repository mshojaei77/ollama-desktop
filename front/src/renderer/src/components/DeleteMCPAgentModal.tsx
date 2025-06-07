import React, { useState } from 'react'
import { Trash2, AlertTriangle, X } from 'lucide-react'
import { MCPAgent } from '../services/mcpAgentService'

interface DeleteMCPAgentModalProps {
  agent: MCPAgent
  onClose: () => void
  onDelete: (agentId: string, permanent: boolean) => Promise<void>
}

const DeleteMCPAgentModal: React.FC<DeleteMCPAgentModalProps> = ({
  agent,
  onClose,
  onDelete
}) => {
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await onDelete(agent.id, true) // Always permanent delete
      onClose()
    } catch (error) {
      console.error('Error deleting agent:', error)
      alert('Failed to delete agent. Please try again.')
    } finally {
      setIsDeleting(false)
    }
  }

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-lg max-w-md w-full p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-[hsl(var(--foreground))] flex items-center gap-2">
            <Trash2 className="w-5 h-5 text-red-500" />
            Delete Agent
          </h2>
          <button
            onClick={onClose}
            className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] p-1 rounded transition-colors"
            disabled={isDeleting}
          >
            <X size={20} />
          </button>
        </div>

        <div className="mb-6">
          <p className="text-[hsl(var(--muted-foreground))] mb-2">
            Are you sure you want to delete this agent?
          </p>
          <div className="bg-[hsl(var(--accent))]/20 border border-[hsl(var(--border))] rounded p-3 mb-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                {agent.icon ? (
                  agent.icon.startsWith('./') || agent.icon.startsWith('/') || 
                  agent.icon.includes('.png') || agent.icon.includes('.jpg') || 
                  agent.icon.includes('.svg') ? (
                    <img 
                      src={agent.icon} 
                      alt={agent.name}
                      className="w-8 h-8 object-contain"
                    />
                  ) : (
                    <span className="text-lg">{agent.icon}</span>
                  )
                ) : (
                  <div className="w-8 h-8 rounded bg-[hsl(var(--primary))]/10 flex items-center justify-center">
                    <span className="text-xs text-[hsl(var(--primary))]">🤖</span>
                  </div>
                )}
              </div>
              <div>
                <p className="font-medium text-[hsl(var(--foreground))]">{agent.name}</p>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">{agent.description}</p>
                <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">
                  {agent.model_provider}/{agent.model_name}
                </p>
              </div>
            </div>
          </div>

          {/* Simple Confirmation */}
          <div className="p-3 border border-red-500/30 rounded bg-red-500/5">
            <div className="font-medium text-red-400 flex items-center gap-2 mb-2">
              <AlertTriangle size={16} />
              Delete Agent Permanently
            </div>
            <div className="text-sm text-[hsl(var(--muted-foreground))]">
              This will completely remove the agent and all its configuration. 
              This action cannot be undone.
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            disabled={isDeleting}
            className="flex-1 px-4 py-2 border border-[hsl(var(--border))] rounded-md text-[hsl(var(--foreground))] hover:bg-[hsl(var(--accent))]/20 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="flex-1 px-4 py-2 rounded-md text-white transition-colors disabled:opacity-50 flex items-center justify-center gap-2 bg-red-600 hover:bg-red-700"
          >
            {isDeleting ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <Trash2 size={16} />
                Delete
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default DeleteMCPAgentModal 