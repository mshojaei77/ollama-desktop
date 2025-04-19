export const getModelBaseName = (modelName: string): string => {
  if (modelName.toLowerCase().includes('embed')) {
    return 'embed'
  }

  const nameWithoutTag = modelName.split(':')[0]

  // Get the last part after slash for models with paths
  const repoName = nameWithoutTag.includes('/') 
    ? nameWithoutTag.split('/')[nameWithoutTag.split('/').length - 1] 
    : nameWithoutTag

  if (repoName.includes(' ')) {
    return repoName.split(' ')[0].toLowerCase()
  }

  if (repoName.includes('-')) {
    const part = repoName.split('-')[0]
    const match = part.match(/^([a-zA-Z]+)/)
    return match && match[1] ? match[1].toLowerCase() : part.toLowerCase()
  }

  const match = repoName.match(/^([a-zA-Z]+)/)
  if (match && match[1]) {
    return match[1].toLowerCase()
  }

  return repoName.toLowerCase()
}

// Load model and agent icon modules eagerly
const modelIconModules = import.meta.glob('./assets/models/*.png', { eager: true, as: 'url' }) as Record<string, string>
const agentIconModules = import.meta.glob('./assets/agents/*.png', { eager: true, as: 'url' }) as Record<string, string>

// Replace getIconPath to fallback to default.png when no specific icon found
export const getIconPath = (modelName: string): string => {
  const baseName = getModelBaseName(modelName)
  const relativePath = `./assets/models/${baseName}.png`
  return modelIconModules[relativePath] || modelIconModules['./assets/models/default.png']
}

// Replace getAgentIconPath to fallback to default.png when no specific agent icon found
export const getAgentIconPath = (agentId: string): string => {
  const relativePath = `./assets/agents/${agentId}.png`
  return agentIconModules[relativePath] || modelIconModules['./assets/models/default.png']
}

export const getModelDisplayName = (modelName: string): string => {
  // First, remove any tags (e.g., ":latest")
  const nameWithoutTag = modelName.split(':')[0];
  
  // If there are slashes, get the last part after the slash
  if (nameWithoutTag.includes('/')) {
    const parts = nameWithoutTag.split('/');
    return parts[parts.length - 1];
  }
  
  return modelName;
}

export const copyToClipboardWithFeedback = (content: string, element: HTMLButtonElement): void => {
  navigator.clipboard
    .writeText(content)
    .then(() => {
      const originalText = element.textContent
      element.textContent = 'Copied!'
      element.classList.add('copied')

      setTimeout(() => {
        element.textContent = originalText
        element.classList.remove('copied')
      }, 2000)
    })
    .catch((err) => {
      console.error('Failed to copy:', err)
      element.textContent = 'Failed!'
      setTimeout(() => {
        element.textContent = 'Copy'
      }, 2000)
    })
}

export const copyToClipboard = (content: string): void => {
  navigator.clipboard
    .writeText(content)
    .then(() => {
      console.log('Content copied to clipboard')
    })
    .catch((err) => {
      console.error('Failed to copy:', err)
    })
}
