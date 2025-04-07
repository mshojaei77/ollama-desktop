import { useState, useEffect } from 'react'
import { Button } from '@renderer/components/ui/button'
import 'highlight.js/styles/github.css'
import 'highlight.js/styles/github-dark.css'
import '../styles/markdown.css'
import { useChatStore } from '../store/chatStore'
import WelcomeNote from './chat/WelcomeNote'
import MessageContainer from './chat/MessageContainer'
import InputSection from './chat/InputSection'
import { checkApiConnection } from '@renderer/fetch/queries'

export default function Chat(): JSX.Element {
  const [apiConnected, setApiConnected] = useState<boolean | null>(null)

  const isSessionActive = useChatStore((state) => state.isSessionActive)

  useEffect(() => {
    const checkConnection = async (): Promise<void> => {
      const isConnected = await checkApiConnection()
      setApiConnected(isConnected)
    }

    checkConnection()
  }, [])
  
  // Apply appropriate syntax highlighting styles based on theme
  useEffect(() => {
    const updateSyntaxTheme = () => {
      const isDarkMode = document.documentElement.classList.contains('dark')
      
      // Get all existing highlight.js stylesheets
      const existingLinks = document.querySelectorAll('link[data-highlight-theme]')
      existingLinks.forEach(link => link.remove())
      
      // Create and append appropriate stylesheet
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.setAttribute('data-highlight-theme', 'true')
      
      if (isDarkMode) {
        link.href = '/highlightjs/github-dark.css'
      } else {
        link.href = '/highlightjs/github.css'
      }
      
      document.head.appendChild(link)
    }
    
    // Run on mount
    updateSyntaxTheme()
    
    // Set up observer to detect theme changes
    const observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        if (mutation.attributeName === 'class' && 
            (mutation.target as Element).classList.contains('dark') !== undefined) {
          updateSyntaxTheme()
        }
      })
    })
    
    observer.observe(document.documentElement, { attributes: true })
    
    // Clean up
    return () => observer.disconnect()
  }, [])

  if (apiConnected === false) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6">
        <div className="text-center max-w-md">
          <h1 className="mb-4 text-2xl font-bold text-red-500">API Connection Error</h1>
          <p className="mb-6">
            Could not connect to the Ollama API server at <code>http://localhost:8000</code>.
          </p>
          <p className="mb-6">Please make sure the API server is running and try again.</p>
          <Button onClick={() => window.location.reload()}>Retry Connection</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full max-h-screen bg-[hsl(var(--background))]">
      {!isSessionActive ? (
        <WelcomeNote apiConnected={apiConnected ?? false} />
      ) : (
        <>
          <MessageContainer />

          <InputSection apiConnected={apiConnected ?? false} />
        </>
      )}
    </div>
  )
} 