export const getModelBaseName = (modelName: string): string => {
  if (modelName.toLowerCase().includes('embed')) {
    return 'embed'
  }

  const nameWithoutTag = modelName.split(':')[0]

  const repoName = nameWithoutTag.includes('/') ? nameWithoutTag.split('/')[1] : nameWithoutTag

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

export const getModelDisplayName = (modelName: string): string => {
  if (modelName.includes('/')) {
    return modelName.split('/')[1]
  }

  return modelName
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
