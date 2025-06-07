import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Send, Paperclip, Image, RefreshCw, Bot, Settings } from 'lucide-react';
import mcpAgentService, { MCPAgent } from '../services/mcpAgentService';
import MessageContainer, { GenericMessage } from '../containers/chat/MessageContainer';

interface Message {
  id: string;
  role: 'user' | 'agent';
  content: string;
  isLoading?: boolean;
  agentId: string;
}

interface MCPAgentChatProps {
  agentId: string;
  onBack: () => void;
}

function MCPAgentChat({ agentId, onBack }: MCPAgentChatProps): JSX.Element {
  const [agent, setAgent] = useState<MCPAgent | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Load agent details
  useEffect(() => {
    const loadAgent = async () => {
      const agentData = await mcpAgentService.getAgentById(agentId);
      if (agentData) {
        console.log('MCP Agent data loaded:', agentData);
        setAgent(agentData);
      }
    };
    
    loadAgent();
  }, [agentId]);

  // Focus on input when component mounts
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Cleanup event source on unmount
  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  // Function to handle streaming agent response
  const startAgentResponseStream = (prompt: string) => {
    if (isLoading) return;

    // Close any existing stream
    eventSourceRef.current?.close();
    setIsLoading(true);

    const placeholderId = crypto.randomUUID();
    // Add placeholder message
    setMessages(prev => [...prev, { id: placeholderId, role: 'agent', content: '', isLoading: true, agentId: agentId }]);

    const eventSource = mcpAgentService.streamMessage(agentId, { message: prompt });
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.done) {
          // Streaming complete - update message isLoading flag
          setMessages(prev => prev.map(msg =>
            msg.id === placeholderId ? { ...msg, isLoading: false, agentId: agentId } : msg
          ));
          eventSource.close();
          setIsLoading(false);
          eventSourceRef.current = null;
        } else if (data.text) {
          // Update the streaming response by ID
          setMessages(prev => prev.map(msg =>
            msg.id === placeholderId ? { ...msg, content: msg.content + data.text, isLoading: true, agentId: agentId } : msg
          ));
        } else if (data.error) {
          // Handle error - update message content and isLoading flag
          console.error('Error from MCP agent:', data.error);
          setMessages(prev => prev.map(msg =>
            msg.id === placeholderId ? { ...msg, content: 'Sorry, I encountered an error processing your request.', isLoading: false, agentId: agentId } : msg
          ));
          eventSource.close();
          setIsLoading(false);
          eventSourceRef.current = null;
        }
      } catch (error) {
        console.error('Error parsing SSE message:', error, event.data);
         // Handle parsing error - update message content and isLoading flag
         setMessages(prev => prev.map(msg =>
           msg.id === placeholderId ? { ...msg, content: 'Sorry, I encountered an error receiving the response.', isLoading: false, agentId: agentId } : msg
         ));
         eventSource.close();
         setIsLoading(false);
         eventSourceRef.current = null;
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      // Handle connection error - update message content and isLoading flag
      setMessages(prev => prev.map(msg =>
        msg.id === placeholderId ? { ...msg, content: 'Sorry, I encountered a connection error. Please try again.', isLoading: false, agentId: agentId } : msg
      ));
      eventSource.close();
      setIsLoading(false);
      eventSourceRef.current = null;
    };
  };

  // Handle message submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;

    // Add user message to chat
    const userMessage: Message = { id: crypto.randomUUID(), role: 'user', content: trimmedInput, agentId };
    setMessages(prev => [...prev, userMessage]);

    // Clear input
    setInput('');

    // Start agent response stream
    startAgentResponseStream(trimmedInput);
  };

  // Handle regeneration request
  const handleRegenerate = (agentMsgId: string) => {
    if (isLoading) return;

    const agentMsgIndex = messages.findIndex(msg => msg.id === agentMsgId);

    // Ensure the message exists and has a preceding user message
    if (agentMsgIndex < 1 || messages[agentMsgIndex - 1]?.role !== 'user') {
      console.error("Cannot regenerate: No preceding user message found.");
      return;
    }

    const userMessage = messages[agentMsgIndex - 1];
    const userPrompt = userMessage.content;

    // Remove the agent message to be regenerated and any subsequent messages
    setMessages(prev => prev.slice(0, agentMsgIndex));

    // Start a new agent response stream with the original user prompt
    startAgentResponseStream(userPrompt);
  };

  // Handle input changes and adjust textarea height
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize logic with min-height enforcement
    const textarea = e.target;
    textarea.style.height = 'auto'; // Reset height to recalculate scrollHeight
    // Ensure height is at least min-height (matches CSS min-h-[28px])
    const minHeight = 28;
    textarea.style.height = `${Math.max(textarea.scrollHeight, minHeight)}px`;
  };

  // Adjust textarea height on input change with min-height
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'; // Reset height
      const minHeight = 28; // Match the min-h-[28px] in CSS
      inputRef.current.style.height = `${Math.max(inputRef.current.scrollHeight, minHeight)}px`;
    }
  }, [input]); // Rerun when input changes

  // Handle key press (Enter to send, Shift+Enter for new line)
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Function to detect if text contains Persian or Arabic characters
  const containsRTLText = (text: string): boolean => {
    const rtlRegex = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
    return rtlRegex.test(text);
  };

  return (
    <div className="flex flex-col h-full bg-background shadow-lg rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex items-center p-4 border-b border-border bg-primary text-primary-foreground">
        <button 
          onClick={onBack}
          className="mr-3 text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft size={20} />
        </button>
        
        {agent && (
          <div className="flex items-center flex-1">
            <div className="flex-shrink-0 mr-3">
              {agent.icon ? (
                <img 
                  src={agent.icon}
                  alt={agent.name}
                  className="w-10 h-10 rounded-full"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = `https://via.placeholder.com/40x40?text=${encodeURIComponent(agent.name[0])}&quality=100`;
                  }}
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-primary-foreground/20 flex items-center justify-center">
                  <Bot className="w-6 h-6 text-primary-foreground" />
                </div>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-foreground truncate">{agent.name}</h3>
              <p className="text-xs text-muted-foreground truncate">{agent.description}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs bg-primary-foreground/20 text-primary-foreground px-2 py-0.5 rounded">
                  {agent.model_provider}/{agent.model_name}
                </span>
                {agent.mcp_servers.length > 0 && (
                  <span className="text-xs bg-primary-foreground/20 text-primary-foreground px-2 py-0.5 rounded">
                    {agent.mcp_servers.length} MCP Server{agent.mcp_servers.length > 1 ? 's' : ''}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Messages */}
      {messages.length === 0 && agent ? (
        <div className="flex-1 overflow-y-auto p-4 flex flex-col items-center justify-center text-center bg-background-light">
          <div className="mb-4 p-3 bg-primary-foreground rounded-full inline-flex items-center justify-center shadow-md">
            {agent.icon ? (
              <img 
                src={agent.icon}
                alt={agent.name}
                className="w-12 h-12"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = `https://via.placeholder.com/48x48?text=${encodeURIComponent(agent.name[0])}&quality=100`;
                }}
              />
            ) : (
              <Bot className="w-12 h-12 text-primary" />
            )}
          </div>
          <h2 className="text-2xl font-bold text-foreground mb-1">
            {agent.name}
          </h2>
          <p className="text-sm text-muted-foreground mb-2 max-w-md">
            {agent.description}
          </p>
          {agent.mcp_servers.length > 0 && (
            <p className="text-xs text-muted-foreground mb-6">
              Connected to {agent.mcp_servers.length} MCP server{agent.mcp_servers.length > 1 ? 's' : ''} • 
              Model: {agent.model_provider}/{agent.model_name}
            </p>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-xl">
            {(agent.example_prompts && agent.example_prompts.length > 0 ? agent.example_prompts : [
              "How can you help me?",
              "What capabilities do you have?",
              "What MCP servers are you connected to?",
              "Tell me about your features"
            ]).map((prompt, index) => (
              <button
                key={index}
                onClick={() => {
                  setInput(prompt);
                  inputRef.current?.focus();
                }}
                className="border border-border/80 rounded-lg p-3 text-left text-foreground bg-card hover:border-primary hover:bg-card/80 transition-colors text-sm flex-grow"
                style={{
                  fontFamily: containsRTLText(prompt) ? "'Vazir', sans-serif" : 'inherit',
                  direction: containsRTLText(prompt) ? 'rtl' : 'ltr',
                  textAlign: containsRTLText(prompt) ? 'right' : 'left'
                }}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <MessageContainer
          messages={messages as GenericMessage[]}
          isStreaming={isLoading}
          onRefresh={handleRegenerate}
        />
      )}
      
      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 bg-background-light">
        <div className="flex items-end gap-2 bg-background rounded-lg py-1 px-3 shadow-inner border border-border/30">
          <textarea
            ref={inputRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            placeholder="Ask anything"
            className="flex-1 bg-transparent focus:outline-none text-foreground placeholder-muted-foreground resize-none overflow-hidden max-h-[120px] py-1.5 min-h-[28px] self-center"
            disabled={isLoading}
            rows={1}
            style={{
              fontFamily: containsRTLText(input) ? "'Vazir', sans-serif" : 'inherit',
              direction: containsRTLText(input) ? 'rtl' : 'ltr',
              textAlign: containsRTLText(input) ? 'right' : 'left',
            }}
          />
          <div className="flex-shrink-0 flex items-center space-x-0.5 mb-0.5">
            <button
              type="button"
              disabled={isLoading}
              className="p-1.5 text-muted-foreground hover:text-primary disabled:text-gray-500 rounded-md hover:bg-muted"
              aria-label="Attach file"
            >
              <Paperclip size={16} />
            </button>
            <button
              type="button"
              disabled={isLoading}
              className="p-1.5 text-muted-foreground hover:text-primary disabled:text-gray-500 rounded-md hover:bg-muted"
              aria-label="Attach image"
            >
              <Image size={16} />
            </button>
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="p-1.5 text-primary disabled:text-muted-foreground rounded-md hover:bg-muted"
              aria-label="Send message"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

export default MCPAgentChat; 