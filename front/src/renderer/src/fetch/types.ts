export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

// API response message format
export interface ApiMessage {
  id: string
  role: 'user' | 'assistant'
  message: string
  timestamp: string
}

export interface ChatSession {
  id: string
  model: string
}

export interface ModelOption {
  name: string
  description?: string
}

export interface InitializeChatParams {
  model_name: string
  system_message?: string
}

export interface InitializeChatResponse {
  model_name: string
  system_message?: string
  session_id: string
}

export interface SendMessageParams {
  message: string
  session_id: string
}

export interface SendMessageResponse {
  response: string
}

export interface ModelsResponse {
  models: string[]
}

export interface ChatHistoryResponse {
  history: ApiMessage[]
  session_id: string
  count: number
}

export interface APIChat {
  session_id: string
  model_name: string
  session_type: string
  system_message?: string
  created_at: string
  last_active: string
  is_active: boolean
  message_count: number
  first_message_time?: string
  last_message_time?: string
}

export interface AvailableChatsResponse {
  sessions: APIChat[]
  count: number
}

export interface DisplayedChatSession {
  id: string
  title: string
  lastMessage?: string
  timestamp?: Date
  messageCount: number
}

export interface MessageActionProps {
  message: Message
  onCopy: (content: string) => void
  onRefresh: (id: string) => void
}

export interface MCPServersResponse {
  servers: Record<string, MCPServer>
}

export interface MCPServer {
  type?: string
  tools?: string[] | string
  command?: string
  [key: string]: unknown
}

export interface NewServerForm {
  name: string
  command: string
  type: string
}
