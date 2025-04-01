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
  clearMessages: () => void
  setSelectedModel: (model: string) => void
}

export const useChatStore = create<ChatState>((set) => ({
  // Initial state
  sessionId: null,
  modelName: '',
  isSessionActive: false,
  messages: [],
  selectedModel: 'llama3.2',

  // Actions
  setSessionId: (sessionId: string | null): void => set({ sessionId }),
  setModelName: (modelName: string): void => set({ modelName }),
  setSessionActive: (active: boolean): void => set({ isSessionActive: active }),
  setMessages: (messages: Message[]): void => set({ messages }),
  addMessage: (message: Message): void =>
    set((state) => ({
      messages: [...state.messages, message]
    })),
  clearMessages: (): void => set({ messages: [] }),
  setSelectedModel: (model: string): void => set({ selectedModel: model })
}))
