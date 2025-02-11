'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MessageSquare, Plus, Send, Users } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';

export default function ChatComponent() {
  type Agent = {
    id: number;
    name: string;
    description: string;
    agent_type: string;
  };

  type Conversation = {
    id: string;
    title: string;
  };
  
  type Message = {
    id?: number;
    role: 'user' | 'assistant';
    content: string;
    pending?: boolean;
  };
  
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async (): Promise<void> => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/agent/get-all`);
      if (!response.ok) throw new Error('Failed to fetch agents');
      const data: Agent[] = await response.json();
      setAgents(data);
    } catch (error) {
      setError('Failed to load agents');
      console.error('Error:', error);
    }
  };

  const fetchConversations = async (agentId: number): Promise<void> => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/chat/conversations?agent_id=${agentId}`);
      if (!response.ok) throw new Error('Failed to fetch conversations');
      const data: Conversation[] = await response.json();
      setConversations(data);
    } catch (error) {
      setError('Failed to load conversations');
      console.error('Error:', error);
    }
  };

  const createNewConversation = async () => {
    if (!selectedAgent) return;
    
    try {
      const response = await fetch(`${BACKEND_API_URL}/chat/conversations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `Chat with ${selectedAgent.name}`,
          agent_ids: [selectedAgent.id]
        }),
      });
      if (!response.ok) throw new Error('Failed to create conversation');
      const newConversation = await response.json();
      setConversations([...conversations, newConversation]);
      setCurrentConversation(newConversation);
      setMessages([]); // Clear messages for new conversation
    } catch (error) {
      setError('Failed to create new conversation');
      console.error('Error:', error);
    }
  };

  const sendMessage = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!input.trim() || !currentConversation || !selectedAgent) return;
    
    // Immediately add user message to UI
    const userMessage: Message = {
      role: 'user',
      content: input,
    };
    
    // Add loading message placeholder
    const loadingMessage: Message = {
      role: 'assistant',
      content: 'Thinking...',
      pending: true,
    };
    
    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${BACKEND_API_URL}/chat/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: currentConversation.id,
          role: 'user',
          content: input,
          agent_id: selectedAgent.id
        }),
      });
      
      if (!response.ok) throw new Error('Failed to send message');
      const newMessage = await response.json();
      
      // Remove loading message and add actual response
      setMessages(prev => {
        const filtered = prev.filter(msg => !msg.pending);
        return [...filtered, {
          role: 'assistant',
          content: newMessage.content,
          id: newMessage.id
        }];
      });
    } catch (error) {
      setError('Failed to send message');
      console.error('Error:', error);
      // Remove loading message if there was an error
      setMessages(prev => prev.filter(msg => !msg.pending));
    } finally {
      setLoading(false);
    }
  };

  const selectConversation = async (conversation: Conversation): Promise<void> => {
    setCurrentConversation(conversation);
    try {
      const response = await fetch(`${BACKEND_API_URL}/chat/conversations/${conversation.id}`);
      if (!response.ok) throw new Error('Failed to fetch conversation');
      const data: { messages: Message[] } = await response.json();
      setMessages(data.messages || []);
    } catch (error) {
      setError('Failed to load conversation');
      console.error('Error:', error);
    }
  };

  const handleAgentSelect = (agentId: string) => {
    const agent = agents.find(a => a.id === parseInt(agentId));
    if (agent) {
      setSelectedAgent(agent);
      setCurrentConversation(null);
      setMessages([]);
      fetchConversations(agent.id);
    }
  };

  const MessageComponent = ({ message }: { message: Message }) => (
    <div
      className={`flex ${
        message.role === 'user' ? 'justify-end' : 'justify-start'
      }`}
    >
      <div
        className={`max-w-[80%] rounded-lg p-3 ${
          message.role === 'user'
            ? 'bg-blue-500 text-white'
            : message.pending
            ? 'bg-gray-100 animate-pulse'
            : 'bg-gray-100'
        }`}
      >
        {message.content}
      </div>
    </div>
  );

  return (
    <div className="flex h-[calc(100vh-4rem)] max-w-6xl mx-auto">
      {/* Sidebar */}
      <div className="w-64 border-r bg-gray-50 p-4">
        {/* Agent Selection */}
        <div className="mb-6">
          <Select onValueChange={handleAgentSelect}>
            <SelectTrigger>
              <SelectValue placeholder="Select an agent" />
            </SelectTrigger>
            <SelectContent>
              {agents.map((agent) => (
                <SelectItem key={agent.id} value={agent.id.toString()}>
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    {agent.name}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {selectedAgent && (
          <>
            <Button 
              className="w-full mb-4" 
              onClick={createNewConversation}
            >
              <Plus className="w-4 h-4 mr-2" />
              New Chat
            </Button>
            
            <div className="space-y-2">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`p-2 rounded cursor-pointer flex items-center gap-2 ${
                    currentConversation?.id === conv.id 
                      ? 'bg-blue-100' 
                      : 'hover:bg-gray-100'
                  }`}
                  onClick={() => selectConversation(conv)}
                >
                  <MessageSquare className="w-4 h-4" />
                  <span className="truncate">{conv.title}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {!selectedAgent && (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Please select an agent to start chatting
          </div>
        )}

        {selectedAgent && (
          <>
            {error && (
              <div className="bg-red-100 text-red-700 p-2 text-center">
                {error}
              </div>
            )}
            
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message, index) => (
                <MessageComponent key={message.id || index} message={message} />
              ))}
            </div>

            <form 
              onSubmit={sendMessage} 
              className="p-4 border-t flex gap-2"
            >
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                disabled={!currentConversation || loading}
                className="flex-1"
              />
              <Button 
                type="submit"
                disabled={!currentConversation || loading || !input.trim()}
              >
                <Send className="w-4 h-4" />
              </Button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}