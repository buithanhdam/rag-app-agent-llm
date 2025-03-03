'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MessageSquare, Plus, Send, Users, User } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Markdown from 'react-markdown'
const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';
type MessageType = 'agent' | 'communication';

export default function ChatComponent() {
  type Agent = {
    id: number;
    name: string;
    description: string;
    agent_type: string;
  };

  type Communication = {
    id: number;
    name: string;
    description: string;
    agents: Agent[];
  };

  type Message = {
    id?: number;
    role: 'user' | 'assistant';
    content: string;
    pending?: boolean;
  };

  type Conversation = {
    id: string;
    title: string;
    messages:Message[]
  };
  
  
  const [agents, setAgents] = useState<Agent[]>([]);
  const [communications, setCommunications] = useState<Communication[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [selectedCommunication, setSelectedCommunication] = useState<Communication | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [chatMode, setChatMode] = useState<'agent' | 'communication'>('agent');

  useEffect(() => {
    fetchAgents();
    fetchCommunications();
  }, []);

  useEffect(() => {
    if (selectedAgent?.id) {
      fetchConversations(selectedAgent.id, true);
    }
  }, [selectedAgent]);
  
  useEffect(() => {
    if (selectedCommunication?.id) {
      fetchConversations(selectedCommunication.id, false);
    }
  }, [selectedCommunication]);

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

  const fetchMessagesByConversation = async (conversation: Conversation): Promise<void> => {
    try{
      const response = await fetch(`${BACKEND_API_URL}/chat/chat/get-all?conversation_id=${conversation.id}`);
      if (!response.ok) throw new Error('Failed to fetch messages');
      const data: Message[] = await response.json();
      setMessages(data);
    }catch (error) {
      setError('Failed to load messages');
      console.error('Error:', error);
    }
  };
  const fetchCommunications = async (): Promise<void> => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/communication`);
      if (!response.ok) throw new Error('Failed to fetch communications');
      const data: Communication[] = await response.json();
      setCommunications(data);
    } catch (error) {
      setError('Failed to load communications');
      console.error('Error:', error);
    }
  };
  // console.log(chatMode)
  // console.log(selectedCommunication)
  // console.log(selectedAgent)
  const fetchConversations = async (id: number | undefined, is_agent: boolean = true): Promise<void> => {
  if (!id) return; // Ngăn chặn gọi API nếu id chưa có

  try {
    let url = is_agent
      ? `${BACKEND_API_URL}/chat/conversations/agent/get-all?agent_id=${id}`
      : `${BACKEND_API_URL}/chat/conversations/communication/get-all?communication_id=${id}`;

    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch conversations');

    const data: Conversation[] = await response.json();
    setConversations(data);
  } catch (error) {
    setError('Failed to load conversations');
    console.error('Error:', error);
  }
};

  const createNewConversation = async () => {
    if (!selectedAgent && !selectedCommunication) return;
    
    try {
      let url = '';
      let body = {};
      
      if (chatMode === 'agent' && selectedAgent) {
        url = `${BACKEND_API_URL}/chat/conversations/agent/create`;
        body = {
          title: `Conversation ${conversations.length+1} ${selectedAgent.name}`,
          agent_id: selectedAgent.id
        };
      } else if (chatMode === 'communication' && selectedCommunication) {
        url = `${BACKEND_API_URL}/chat/conversations/communication/create`;
        body = {
          communication_id: selectedCommunication.id,
          title: `Conversation ${conversations.length+1} ${selectedCommunication.name}`
        };
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      
      if (!response.ok) throw new Error('Failed to create conversation');
      const newConversation = await response.json();
      setConversations([...conversations, newConversation]);
      setCurrentConversation(newConversation);
      setMessages([]);
    } catch (error) {
      setError('Failed to create new conversation');
      console.error('Error:', error);
    }
  };

  const sendMessage = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!input.trim() || !currentConversation) return;
    
    const userMessage: Message = {
      role: 'user',
      content: input,
    };
    
    const loadingMessage: Message = {
      role: 'assistant',
      content: 'Thinking...',
      pending: true,
    };
    
    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setInput('');
    setLoading(true);

    try {
      const messageData = {
        conversation_id: currentConversation.id,
        role: 'user',
        content: input,
        ...(chatMode === 'agent' && selectedAgent 
          ? { type: "agent" }
          : { type: "communication" }
        )
      };

      const response = await fetch(`${BACKEND_API_URL}/chat/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(messageData),
      });
      
      if (!response.ok) throw new Error('Failed to send message');
      const newMessage = await response.json();
      
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
      setMessages(prev => prev.filter(msg => !msg.pending));
    } finally {
      setLoading(false);
    }
  };

  const handleModeChange = (mode: 'agent' | 'communication') => {
    setChatMode(mode);
    setSelectedAgent(null);
    setSelectedCommunication(null);
    setCurrentConversation(null);
    setMessages([]);
    setConversations([]);
  };

  const MessageComponent = ({ message }: { message: Message }) => (
    <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] rounded-lg p-3 ${
        message.role === 'user'
          ? 'bg-blue-500 text-white'
          : message.pending
          ? 'bg-gray-100 animate-pulse'
          : 'bg-gray-100'
      }`}>
        <Markdown>{message.content}</Markdown>
      </div>
    </div>
  );

  return (
    <div className="flex h-[calc(100vh-4rem)] max-w-6xl mx-auto">
      <div className="w-64 border-r bg-gray-50 p-4">
        <Tabs defaultValue="agent" className="mb-6" onValueChange={(v) => handleModeChange(v as 'agent' | 'communication')}>
          <TabsList className="w-full">
            <TabsTrigger value="agent" className="flex-1">
              <User className="w-4 h-4 mr-2" />
              Agent
            </TabsTrigger>
            <TabsTrigger value="communication" className="flex-1">
              <Users className="w-4 h-4 mr-2" />
              Group
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {chatMode === 'agent' ? (
          <Select onValueChange={(value) => {
            const agent= agents.find(a => a.id === parseInt(value));
            setSelectedAgent(agent || null);
            setCurrentConversation(null);setMessages([]);setConversations([]); 
          }}>
            <SelectTrigger>
              <SelectValue placeholder="Select an agent" />
            </SelectTrigger>
            <SelectContent>
              {agents.map((agent) => (
                <SelectItem key={agent.id} value={agent.id.toString()}>
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4" />
                    {agent.name}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <Select onValueChange={(value) => {
            const comm = communications.find(c => c.id === parseInt(value));
            setSelectedCommunication(comm || null);
            setCurrentConversation(null);setMessages([]);setConversations([]); 
          }}>
            <SelectTrigger>
              <SelectValue placeholder="Select a group" />
            </SelectTrigger>
            <SelectContent>
              {communications.map((comm) => (
                <SelectItem key={comm.id} value={comm.id.toString()}>
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    {comm.name}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {(selectedAgent || selectedCommunication) && (
          <>
            <Button className="w-full my-4" onClick={createNewConversation}>
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
                  onClick={() => {
                    setCurrentConversation(conv);
                    setMessages(conv.messages)
                  }}
                >
                  <MessageSquare className="w-4 h-4" />
                  <span className="truncate">{conv.title}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      <div className="flex-1 flex flex-col">
        {!selectedAgent && !selectedCommunication && (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Please select an {chatMode === 'agent' ? 'agent' : 'group'} to start chatting
          </div>
        )}

        {(selectedAgent || selectedCommunication) && (
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

            <form onSubmit={sendMessage} className="p-4 border-t flex gap-2">
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