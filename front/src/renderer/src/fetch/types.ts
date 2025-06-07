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
  /** The text of the user message to send or regenerate. */
  message: string
  /** The session ID for this chat. */
  session_id: string
  /** If true, skip automatically re-adding the user message (used for regenerations). */
  skipUser?: boolean
}

export interface SendMessageResponse {
  response: string
}

export interface ModelInfo {
  name: string
  // Add other potential fields from Ollama API response if needed later
  // size?: number;
  // modified_at?: string;
  // digest?: string;
}

export interface ModelsResponse {
  models: ModelInfo[]
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

// Interface for detailed model information
export interface ModelDetails {
  family?: string
  parameter_size?: string
  quantization_level?: string
  model_name?: string // This seems redundant if we query by name, but included based on API output
  languages_supported?: string[]
  parameter_count?: number
  size_label?: string
  tags?: string[]
  type?: string
  context_length?: number
  embedding_length?: number
  vocab_size?: number
  // Add any other fields that might be returned
  [key: string]: unknown // Allow for other potential fields
}
