import { create } from 'zustand'
import { Message } from '../fetch/types'

interface ChatState {
  // Session state
  sessionId: string | null
  modelName: string
  isSessionActive: boolean

  // Messages
  messages: Message[]

  // UI state
  selectedModel: string

  // Actions
  setSessionId: (sessionId: string | null) => void
  setModelName: (modelName: string) => void
  setSessionActive: (active: boolean) => void
  setMessages: (messages: Message[]) => void
  addMessage: (message: Message) => void
  updateMessage: (id: string, contentUpdater: (prevContent: string) => string) => void
  clearMessages: () => void
  setSelectedModel: (model: string) => void
}

export const useChatStore = create<ChatState>((set) => ({
  sessionId: null,
  modelName: '',
  isSessionActive: false,
  messages: [],
  selectedModel: 'llama3.2',

  setSessionId: (sessionId: string | null): void => set({ sessionId }),
  setModelName: (modelName: string): void => set({ modelName }),
  setSessionActive: (active: boolean): void => set({ isSessionActive: active }),
  setMessages: (messages: Message[]): void => set({ messages }),
  addMessage: (message: Message): void =>
    set((state) => ({
      messages: [...state.messages, message]
    })),
  updateMessage: (id: string, contentUpdater: (prevContent: string) => string): void =>
    set((state) => ({
      messages: state.messages.map((message) =>
        message.id === id ? { ...message, content: contentUpdater(message.content) } : message
      )
    })),
  clearMessages: (): void => set({ messages: [] }),
  setSelectedModel: (model: string): void => set({ selectedModel: model })
}))
