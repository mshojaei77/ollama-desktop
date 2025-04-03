import { MCPServer } from '@renderer/fetch/types'
import { useState } from 'react'
import { Button } from '@renderer/components/ui/button'
import { Pencil, Trash2 } from 'lucide-react'
import apiClient from '@renderer/fetch/api-client'
import { toast } from 'sonner'
import EditServerDialog from './EditServerDialog'

const ServersTable = ({
  serverName,
  serverConfig,
  onServerUpdated
}: {
  serverName: string
  serverConfig: MCPServer
  onServerUpdated?: () => void
}): JSX.Element => {
  const [isActive, setIsActive] = useState(serverConfig.active !== false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [isToggling, setIsToggling] = useState(false)

  const handleStatusChange = async () => {
    const newStatus = !isActive
    try {
      setIsToggling(true)
      await apiClient.post(`/mcp/servers/toggle-active/${serverName}`, { active: newStatus })
      setIsActive(newStatus)
      toast.success(`Server ${serverName} ${newStatus ? 'activated' : 'deactivated'}`)
      if (onServerUpdated) onServerUpdated()
    } catch (error) {
      console.error('Error updating server status:', error)
      toast.error(`Failed to ${newStatus ? 'activate' : 'deactivate'} server`)
    } finally {
      setIsToggling(false)
    }
  }

  const handleDeleteServer = async () => {
    if (confirm(`Are you sure you want to delete the server "${serverName}"?`)) {
      try {
        setIsDeleting(true)
        await apiClient.delete(`/mcp/servers/${serverName}`)
        toast.success(`Server ${serverName} deleted successfully`)
        if (onServerUpdated) onServerUpdated()
      } catch (error) {
        console.error('Error deleting server:', error)
        toast.error('Failed to delete server')
      } finally {
        setIsDeleting(false)
      }
    }
  }

  return (
    <>
      <div key={serverName} className="bg-white rounded-lg shadow-sm border border-gray-200 transition-all duration-200 hover:shadow-md">
        {/* Server Header Section */}
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <div className={`h-3 w-3 rounded-full ${isActive ? 'bg-green-500' : 'bg-gray-400'} transition-colors duration-300`}></div>
            <h2 className="text-xl font-semibold text-gray-800">{serverName}</h2>
            <span className="bg-gray-200 text-gray-700 px-2 py-0.5 rounded text-sm font-medium">
              {serverConfig.type || 'stdio'}
            </span>
          </div>
          
          <div className="flex items-center gap-3">
            {/* Status Toggle */}
            <button
              disabled={isToggling}
              onClick={handleStatusChange}
              className={`relative inline-flex h-8 w-16 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                isActive ? 'bg-green-500' : 'bg-gray-300'
              } ${isToggling ? 'opacity-70' : ''}`}
            >
              <span className="sr-only">{isActive ? 'Deactivate' : 'Activate'} server</span>
              <span
                className={`pointer-events-none relative inline-block h-7 w-7 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  isActive ? 'translate-x-8' : 'translate-x-0'
                }`}
              >
                {isToggling && (
                  <span className="absolute inset-0 flex items-center justify-center">
                    <span className="h-3 w-3 border-2 border-t-transparent border-green-500 rounded-full animate-spin"></span>
                  </span>
                )}
              </span>
            </button>
            
            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setIsEditDialogOpen(true)}
                className="flex items-center gap-1 text-blue-600 border-blue-200 hover:bg-blue-50 hover:border-blue-300"
              >
                <Pencil className="h-4 w-4" />
                Edit
              </Button>
              
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleDeleteServer}
                disabled={isDeleting}
                className="flex items-center gap-1 text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
              >
                {isDeleting ? (
                  <span className="flex items-center gap-1">
                    <span className="h-3 w-3 border-2 border-t-transparent border-red-500 rounded-full animate-spin"></span>
                    Deleting
                  </span>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Server Details Section */}
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 rounded-b-lg">
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center text-gray-500">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5 mr-1"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947z"
                  clipRule="evenodd"
                />
                <path d="M10 13a3 3 0 100-6 3 3 0 000 6z" />
              </svg>
              <span className="font-medium">Tools:</span>
            </div>
            
            <div className="flex flex-wrap gap-1.5">
              {serverConfig.tools ? (
                Array.isArray(serverConfig.tools) ? (
                  serverConfig.tools.map((tool: string, index: number) => (
                    <span key={index} className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-sm font-medium">
                      {tool}
                    </span>
                  ))
                ) : (
                  <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-sm font-medium">
                    {typeof serverConfig.tools === 'string'
                      ? serverConfig.tools
                      : 'sequentialthinking'}
                  </span>
                )
              ) : (
                <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-sm font-medium">
                  {serverName === 'sequential'
                    ? 'sequentialthinking'
                    : serverName === 'web research'
                      ? 'search_google visit_page take_screenshot'
                      : 'unknown'}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Edit Dialog */}
      {isEditDialogOpen && (
        <EditServerDialog 
          isDialogOpen={isEditDialogOpen} 
          setIsDialogOpen={setIsEditDialogOpen} 
          serverName={serverName}
          serverConfig={serverConfig}
          onServerUpdated={onServerUpdated}
        />
      )}
    </>
  )
}

export default ServersTable
