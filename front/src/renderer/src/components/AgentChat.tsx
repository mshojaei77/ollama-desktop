import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Send } from 'lucide-react';
import agentService, { Agent } from '../services/agentService';
import { getAgentIconPath } from '../utils';

interface Message {
  role: 'user' | 'agent';
  content: string;
  isLoading?: boolean;
}

interface AgentChatProps {
  agentId: string;
  onBack: () => void;
}

function AgentChat({ agentId, onBack }: AgentChatProps): JSX.Element {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Load agent details
  useEffect(() => {
    const loadAgent = async () => {
      const agentData = await agentService.getAgentById(agentId);
      if (agentData) {
        setAgent(agentData);
      }
    };
    
    loadAgent();
  }, [agentId]);

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus on input when component mounts
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Handle message submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isLoading) return;
    
    // Add user message to chat
    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    
    // Clear input and set loading state
    setInput('');
    setIsLoading(true);
    
    // Add placeholder for agent response
    setMessages(prev => [...prev, { role: 'agent', content: '', isLoading: true }]);
    
    // Create an event source
    const eventSource = agentService.streamMessage(agentId, { message: input });
    
    // Handle incoming messages
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.done) {
          // Streaming complete
          eventSource.close();
          setIsLoading(false);
        } else if (data.text) {
          // Update the streaming response
          setMessages(prev => {
            const updatedMessages = [...prev];
            const lastMessageIndex = updatedMessages.length - 1;
            
            // Update the last message, which is the agent's response
            const currentContent = updatedMessages[lastMessageIndex].content;
            updatedMessages[lastMessageIndex] = {
              role: 'agent',
              content: currentContent + data.text
            };
            
            return updatedMessages;
          });
        } else if (data.error) {
          // Handle error
          console.error('Error from agent:', data.error);
          setMessages(prev => {
            const updatedMessages = [...prev];
            const lastMessageIndex = updatedMessages.length - 1;
            
            updatedMessages[lastMessageIndex] = {
              role: 'agent',
              content: 'Sorry, I encountered an error processing your request.'
            };
            
            return updatedMessages;
          });
          
          eventSource.close();
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Error parsing SSE message:', error, event.data);
      }
    };
    
    // Handle errors
    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      
      setMessages(prev => {
        const updatedMessages = [...prev];
        const lastMessageIndex = updatedMessages.length - 1;
        
        updatedMessages[lastMessageIndex] = {
          role: 'agent',
          content: 'Sorry, I encountered a connection error. Please try again.'
        };
        
        return updatedMessages;
      });
      
      eventSource.close();
      setIsLoading(false);
    };
    
    // Clean up event source when component unmounts
    return () => {
      eventSource.close();
    };
  };

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  // Handle key press (Enter to send, Shift+Enter for new line)
  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="flex items-center p-4 border-b border-border">
        <button 
          onClick={onBack}
          className="mr-3 text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft size={20} />
        </button>
        
        {agent && (
          <div className="flex items-center">
            <img 
              src={getAgentIconPath(agent.id)}
              alt={agent.name}
              className="w-8 h-8 rounded-full mr-3"
              onError={(e) => {
                // If icon from local assets fails, try the URL from agent metadata
                (e.target as HTMLImageElement).src = agent.icon || 'https://via.placeholder.com/200?text=' + encodeURIComponent(agent.name[0]);
              }}
            />
            <div>
              <h3 className="font-medium text-foreground">{agent.name}</h3>
              <p className="text-xs text-muted-foreground">{agent.tags.join(', ')}</p>
            </div>
          </div>
        )}
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <h3 className="text-xl font-semibold text-foreground mb-2">
              {agent?.name || 'Agent'} is ready to assist you
            </h3>
            <p className="text-muted-foreground max-w-md">
              {agent?.description || 'Ask a question to get started.'}
            </p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div 
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div 
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === 'user' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-muted text-foreground'
                }`}
              >
                {message.isLoading ? (
                  <div className="flex space-x-2 items-center">
                    <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-border">
        <div className="flex items-center relative">
          <textarea
            ref={inputRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            placeholder="Type a message..."
            className="flex-1 bg-background border border-border rounded-md py-2 pl-3 pr-10 resize-none max-h-[120px] min-h-[44px]"
            rows={1}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="absolute right-3 text-primary disabled:text-muted-foreground"
          >
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}

export default AgentChat; 