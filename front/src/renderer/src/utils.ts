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
    return repoName.split('-')[0].toLowerCase()
  }

  const match = repoName.match(/^([a-zA-Z]+)/)
  if (match && match[1]) {
    return match[1].toLowerCase()
  }

  return repoName.toLowerCase()
}

export const getIconPath = (modelName: string): string => {
  const baseName = getModelBaseName(modelName)
  try {
    return new URL(`./assets/models/${baseName}.png`, import.meta.url).href
  } catch {
    return new URL('./assets/models/default.png', import.meta.url).href
  }
}

export const getAgentIconPath = (agentId: string): string => {
  try {
    return new URL(`./assets/agents/${agentId}.png`, import.meta.url).href
  } catch {
    // Return a default icon if the agent icon is not found
    return new URL('./assets/models/default.png', import.meta.url).href
  }
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
