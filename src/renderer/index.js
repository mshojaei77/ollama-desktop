document.addEventListener('DOMContentLoaded', async () => {
    // DOM elements
    const modelSelect = document.getElementById('model-select');
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const pullModelBtn = document.getElementById('pull-model-btn');
    const modelPullModal = document.getElementById('model-pull-modal');
    const closeModalBtn = document.querySelector('.close');
    const newModelNameInput = document.getElementById('new-model-name');
    const confirmPullBtn = document.getElementById('confirm-pull-btn');
    const pullStatus = document.getElementById('pull-status');
  
    // Chat and session state
    let messages = [];
    let currentSessionId = null;
    let isSessionInitializing = false;
  
    // Load available models
    async function loadModels() {
      try {
        const models = await window.api.listModels();
        modelSelect.innerHTML = '';
        
        if (models.error) {
          alert('Error loading models: ' + models.error);
          return;
        }
        
        // Handle the new API response format (array of strings instead of objects)
        models.forEach(model => {
          const option = document.createElement('option');
          // Check if model is a string or an object with a name property
          option.value = typeof model === 'string' ? model : model.name;
          option.textContent = typeof model === 'string' ? model : model.name;
          modelSelect.appendChild(option);
        });
        
        if (models.length > 0) {
          modelSelect.value = typeof models[0] === 'string' ? models[0] : models[0].name;
        }
      } catch (error) {
        console.error('Error loading models:', error);
        alert('Failed to load models. Is the FastAPI server running?');
      }
    }
  
    // Initialize a new chat session
    async function initializeSession() {
      try {
        isSessionInitializing = true;
        
        // Show initialization status
        const loadingElement = document.createElement('div');
        loadingElement.className = 'message system-message';
        loadingElement.textContent = 'Initializing session...';
        chatMessages.appendChild(loadingElement);
        
        const selectedModel = modelSelect.value;
        // Default system message
        const systemMessage = "You are a helpful assistant.";
        
        const result = await window.api.initializeChat({
          model: selectedModel,
          systemMessage: systemMessage
        });
        
        // Remove loading indicator
        chatMessages.removeChild(loadingElement);
        
        if (result.error) {
          alert('Error initializing session: ' + result.error);
          return false;
        }
        
        currentSessionId = result.sessionId;
        
        // Add system message to UI for user awareness
        const systemElement = document.createElement('div');
        systemElement.className = 'message system-message';
        systemElement.textContent = `Session initialized with model: ${result.model}`;
        chatMessages.appendChild(systemElement);
        
        return true;
      } catch (error) {
        console.error('Error initializing session:', error);
        alert('Failed to initialize session: ' + error.message);
        return false;
      } finally {
        isSessionInitializing = false;
      }
    }
  
    // Send a message to the model
    async function sendMessage() {
      const userMessage = messageInput.value.trim();
      if (!userMessage) return;
      
      // Initialize session if not already done
      if (!currentSessionId && !isSessionInitializing) {
        const initSuccess = await initializeSession();
        if (!initSuccess) return;
      }
      
      // If still initializing, wait a bit
      if (isSessionInitializing) {
        setTimeout(sendMessage, 500);
        return;
      }
      
      // Add user message to UI
      addMessageToUI('user', userMessage);
      
      // Clear input
      messageInput.value = '';
      
      try {
        // Show loading indicator
        const loadingElement = document.createElement('div');
        loadingElement.className = 'message assistant-message';
        loadingElement.textContent = 'Thinking...';
        chatMessages.appendChild(loadingElement);
        
        // Call API with session ID
        const response = await window.api.chat({
          sessionId: currentSessionId,
          message: userMessage
        });
        
        // Remove loading indicator
        chatMessages.removeChild(loadingElement);
        
        if (response.error) {
          alert('Error: ' + response.error);
          return;
        }
        
        // Add assistant response to UI
        const assistantMessage = response.response;
        addMessageToUI('assistant', assistantMessage);
        
      } catch (error) {
        console.error('Error sending message:', error);
        alert('Failed to send message: ' + error.message);
      }
    }
  
    // Add a message to the UI
    function addMessageToUI(role, content) {
      const messageElement = document.createElement('div');
      messageElement.className = `message ${role}-message`;
      
      // Create a paragraph for the message text
      const textElement = document.createElement('p');
      textElement.textContent = content;
      messageElement.appendChild(textElement);
      
      chatMessages.appendChild(messageElement);
      
      // Auto scroll to bottom
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  
    // Start a new chat (clear messages and session)
    async function startNewChat() {
      // Clear UI
      chatMessages.innerHTML = '';
      messages = [];
      
      // Close current session if exists
      if (currentSessionId) {
        try {
          await window.api.closeSession({ sessionId: currentSessionId });
        } catch (error) {
          console.error('Error closing session:', error);
        }
      }
      
      currentSessionId = null;
      
      // Initialize new session
      await initializeSession();
    }
  
    // Pull a new model
    async function pullModel(modelName) {
      try {
        pullStatus.textContent = `Pulling model: ${modelName}...`;
        pullStatus.style.backgroundColor = '#fff3cd';
        
        // Not implementing this directly through FastAPI for now
        // We could add a custom endpoint for this if needed
        alert("Model pulling is not implemented in this version. Please pull models using Ollama CLI.");
        pullStatus.textContent = 'Please use Ollama CLI to pull models.';
        pullStatus.style.backgroundColor = '#f8d7da';
        
        // Close the modal
        setTimeout(() => {
          modelPullModal.style.display = 'none';
        }, 3000);
        
      } catch (error) {
        console.error('Error pulling model:', error);
        pullStatus.textContent = `Error: ${error.message}`;
        pullStatus.style.backgroundColor = '#f8d7da';
      }
    }
  
    // Add a button to start a new chat
    const headerDiv = document.querySelector('header');
    const newChatBtn = document.createElement('button');
    newChatBtn.id = 'new-chat-btn';
    newChatBtn.className = 'bg-secondary text-secondary-foreground hover:bg-secondary/90 px-4 py-2 rounded-md text-sm font-medium';
    newChatBtn.textContent = 'New Chat';
    headerDiv.appendChild(newChatBtn);
    
    // Add CSS for system messages
    const style = document.createElement('style');
    style.textContent = `
      .system-message {
        background-color: #f0f0f0;
        color: #666;
        font-style: italic;
        text-align: center;
        padding: 8px;
        margin: 8px 0;
        border-radius: 8px;
      }
    `;
    document.head.appendChild(style);
  
    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  
    newChatBtn.addEventListener('click', startNewChat);
  
    pullModelBtn.addEventListener('click', () => {
      modelPullModal.style.display = 'block';
      newModelNameInput.value = '';
      pullStatus.textContent = '';
      pullStatus.style.backgroundColor = 'transparent';
    });
  
    closeModalBtn.addEventListener('click', () => {
      modelPullModal.style.display = 'none';
    });
  
    window.addEventListener('click', (e) => {
      if (e.target === modelPullModal) {
        modelPullModal.style.display = 'none';
      }
    });
  
    confirmPullBtn.addEventListener('click', () => {
      const modelName = newModelNameInput.value.trim();
      if (modelName) {
        pullModel(modelName);
      } else {
        alert('Please enter a model name');
      }
    });
  
    // Initialize
    await loadModels();
    
    // Update preload.js API expectations
    console.log("Remember to update the preload.js file to expose the required API methods!");
});