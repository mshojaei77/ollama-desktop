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
  
    // Chat history
    let messages = [];
  
    // Load available models
    async function loadModels() {
      try {
        const models = await window.api.listModels();
        modelSelect.innerHTML = '';
        
        if (models.error) {
          alert('Error loading models: ' + models.error);
          return;
        }
        
        models.forEach(model => {
          const option = document.createElement('option');
          option.value = model.name;
          option.textContent = model.name;
          modelSelect.appendChild(option);
        });
        
        if (models.length > 0) {
          modelSelect.value = models[0].name;
        }
      } catch (error) {
        console.error('Error loading models:', error);
        alert('Failed to load models. Is Ollama running?');
      }
    }
  
    // Send a message to the model
    async function sendMessage() {
      const userMessage = messageInput.value.trim();
      if (!userMessage) return;
      
      // Add user message to UI
      addMessageToUI('user', userMessage);
      
      // Add to messages array
      messages.push({ role: 'user', content: userMessage });
      
      // Clear input
      messageInput.value = '';
      
      try {
        const selectedModel = modelSelect.value;
        
        // Show loading indicator
        const loadingElement = document.createElement('div');
        loadingElement.className = 'message assistant-message';
        loadingElement.textContent = 'Thinking...';
        chatMessages.appendChild(loadingElement);
        
        // Call Ollama API
        const response = await window.api.chat({
          model: selectedModel,
          messages: messages
        });
        
        // Remove loading indicator
        chatMessages.removeChild(loadingElement);
        
        if (response.error) {
          alert('Error: ' + response.error);
          return;
        }
        
        // Add assistant response to UI
        const assistantMessage = response.message.content;
        addMessageToUI('assistant', assistantMessage);
        
        // Add to messages array
        messages.push({ role: 'assistant', content: assistantMessage });
        
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
  
    // Pull a new model
    async function pullModel(modelName) {
      try {
        pullStatus.textContent = `Pulling model: ${modelName}...`;
        pullStatus.style.backgroundColor = '#fff3cd';
        
        const result = await window.api.pullModel({ model: modelName });
        
        if (result.error) {
          pullStatus.textContent = `Error: ${result.error}`;
          pullStatus.style.backgroundColor = '#f8d7da';
          return;
        }
        
        pullStatus.textContent = 'Model pulled successfully!';
        pullStatus.style.backgroundColor = '#d4edda';
        
        // Reload models list
        await loadModels();
        
      } catch (error) {
        console.error('Error pulling model:', error);
        pullStatus.textContent = `Error: ${error.message}`;
        pullStatus.style.backgroundColor = '#f8d7da';
      }
    }
  
    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  
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
  });