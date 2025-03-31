import React, { useState } from 'react'
import { Input } from '../components/ui/input'
import { Button } from '../components/ui/button'
import { Search, PlusCircle, MessageSquare, Wrench, Settings, Bot } from 'lucide-react'
import ollamaLogo from '../assets/ollama.png'

// This interface defines the structure for a chat session
interface ChatSession {
  id: string
  title: string
}

const Sidebar: React.FC = () => {
  // State for chat sessions and active chat
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([
    { id: '1', title: 'Chat Title' },
    { id: '2', title: 'Chat Title' },
    { id: '3', title: 'Chat Title' },
    { id: '4', title: 'Chat Title' },
    { id: '5', title: 'Chat Title' },
    { id: '6', title: 'Chat Title' }
  ])
  const [activeChat, setActiveChat] = useState<string | null>(null)

  // Handler for creating a new chat
  const handleNewChat = () => {
    const newChat = {
      id: Date.now().toString(),
      title: 'New Chat'
    }
    setChatSessions([newChat, ...chatSessions])
    setActiveChat(newChat.id)
  }

  return (
    <div className="flex flex-col h-screen w-64 bg-white border-r border-gray-200">
      {/* Logo Section */}
      <div className="p-4 flex items-center">
        <div className="font-bold text-xl flex items-center">
          <img src={ollamaLogo} alt="Ollama Logo" className="w-6 h-6 mr-1" />
          ollama desktop
        </div>
      </div>

      {/* Search Bar */}
      <div className="px-4 mb-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
          <Input 
            type="text" 
            placeholder="Search" 
            className="pl-8 bg-gray-100 border-0 h-9"
          />
        </div>
      </div>

      {/* New Chat Button */}
      <div className="px-4 mb-4">
        <Button 
          onClick={handleNewChat}
          className="w-full justify-start bg-white hover:bg-gray-50 text-black border border-gray-200"
        >
          <PlusCircle className="h-4 w-4 mr-2" />
          New Chat
        </Button>
      </div>

      {/* Chat History */}
      <div className="flex-grow overflow-y-auto px-2">
        {chatSessions.map(chat => (
          <div 
            key={chat.id}
            onClick={() => setActiveChat(chat.id)}
            className={`flex items-center p-2 rounded-lg cursor-pointer mb-1 ${
              activeChat === chat.id 
                ? 'bg-gray-100' 
                : 'hover:bg-gray-50'
            }`}
          >
            <MessageSquare className="h-4 w-4 mr-2 text-gray-500" />
            <span className="text-sm text-gray-700 truncate">
              {chat.title}
            </span>
          </div>
        ))}
      </div>

      {/* Navigation Items at Bottom */}
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
    </div>
  )
}

export default Sidebar
