import { Wrench, Settings, Bot } from 'lucide-react'

const FooterSection = (): JSX.Element => {
  return (
    <div className="p-2 space-y-1 border-t border-gray-200">
      <div className="flex items-center p-2 rounded-lg cursor-pointer hover:bg-gray-50">
        <Wrench className="h-4 w-4 mr-2 text-gray-500" />
        <span className="text-sm text-gray-700">MCP Servers</span>
      </div>
      <div className="flex items-center p-2 rounded-lg cursor-pointer hover:bg-gray-50">
        <Bot className="h-4 w-4 mr-2 text-gray-500" />
        <span className="text-sm text-gray-700">Agents</span>
      </div>
      <div className="flex items-center p-2 rounded-lg cursor-pointer hover:bg-gray-50">
        <Settings className="h-4 w-4 mr-2 text-gray-500" />
        <span className="text-sm text-gray-700">Settings</span>
      </div>
    </div>
  )
}

export default FooterSection
