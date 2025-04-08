import { useState, useEffect } from 'react'
import { Button } from '@renderer/components/ui/button'
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
      
      // Instead of loading external stylesheets that trigger CSP errors,
      // add inline styles for syntax highlighting
      const styleElement = document.getElementById('highlight-theme-style') || document.createElement('style')
      styleElement.id = 'highlight-theme-style'
      
      // Basic styles for code highlighting that won't trigger CSP errors
      if (isDarkMode) {
        styleElement.textContent = `
          pre code.hljs { display: block; overflow-x: auto; padding: 1em; }
          code.hljs { padding: 3px 5px; }
          .hljs { color: #e6e6e6; background: #1f1f1f; }
          .hljs-comment, .hljs-quote { color: #7f7f7f; }
          .hljs-keyword, .hljs-selector-tag { color: #cc99cd; }
          .hljs-string, .hljs-attr { color: #7ec699; }
          .hljs-number, .hljs-literal { color: #f08d49; }
          .hljs-title, .hljs-section, .hljs-selector-id { color: #f8c555; }
          .hljs-tag, .hljs-name { color: #e2777a; }
          .hljs-attribute { color: #7ec699; }
          .hljs-regexp, .hljs-link { color: #e2777a; }
        `
      } else {
        styleElement.textContent = `
          pre code.hljs { display: block; overflow-x: auto; padding: 1em; }
          code.hljs { padding: 3px 5px; }
          .hljs { color: #24292e; background: #f8f8f8; }
          .hljs-comment, .hljs-quote { color: #6a737d; }
          .hljs-keyword, .hljs-selector-tag { color: #d73a49; }
          .hljs-string, .hljs-attr { color: #032f62; }
          .hljs-number, .hljs-literal { color: #005cc5; }
          .hljs-title, .hljs-section, .hljs-selector-id { color: #6f42c1; }
          .hljs-tag, .hljs-name { color: #22863a; }
          .hljs-attribute { color: #6f42c1; }
          .hljs-regexp, .hljs-link { color: #e36209; }
        `
      }
      
      if (!styleElement.parentNode) {
        document.head.appendChild(styleElement)
      }
    }
    
    // Initial setup
    updateSyntaxTheme()
    
    // Listen for theme changes
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          updateSyntaxTheme()
        }
      })
    })
    
    observer.observe(document.documentElement, { attributes: true })
    
    // Cleanup
    return () => {
      observer.disconnect()
      const styleElement = document.getElementById('highlight-theme-style')
      if (styleElement) styleElement.remove()
    }
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
