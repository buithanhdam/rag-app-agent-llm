'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MessageSquare, Plus, Send } from 'lucide-react';

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';

export default function ChatComponent() {
  type Conversation = {
    id: string;
    title: string;
  };
  
  type Message = {
    role: 'user' | 'assistant';
    content: string;
  };
  
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async (): Promise<void> => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/chat/conversations`);
      if (!response.ok) throw new Error('Failed to fetch conversations');
      const data: Conversation[] = await response.json();
      setConversations(data);
    } catch (error) {
      setError('Failed to load conversations');
      console.error('Error:', error);
    }
  };

  const createNewConversation = async () => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/chat/conversations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: 'New Conversation',
          agent_ids: [] // Add default agent IDs if needed
        }),
      });
      if (!response.ok) throw new Error('Failed to create conversation');
      const newConversation = await response.json();
      setConversations([...conversations, newConversation]);
      setCurrentConversation(newConversation);
    } catch (error) {
      setError('Failed to create new conversation');
      console.error('Error:', error);
    }
  };

  const sendMessage = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!input.trim() || !currentConversation) return;
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_API_URL}/chat/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: currentConversation.id,
          role: 'user',
          content: input,
        }),
      });
      if (!response.ok) throw new Error('Failed to send message');
      const newMessage: Message = await response.json();
      setMessages([...messages, newMessage]);
      setInput('');
    } catch (error) {
      setError('Failed to send message');
      console.error('Error:', error);
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

  return (
    <div className="flex h-[calc(100vh-4rem)] max-w-6xl mx-auto">
      {/* Sidebar */}
      <div className="w-64 border-r bg-gray-50 p-4">
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
              <span className="truncate">{conv.title || 'New Chat'}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {error && (
          <div className="bg-red-100 text-red-700 p-2 text-center">
            {error}
          </div>
        )}
        
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100'
                }`}
              >
                {message.content}
              </div>
            </div>
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
      </div>
    </div>
  );
}