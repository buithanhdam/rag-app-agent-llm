'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Plus, Settings2, Trash2, Save, X, MessageCircle } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';

interface Agent {
  id: number;
  name: string;
  agent_type: string;
  description?: string;
}

interface Communication {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
  configuration: Record<string, any>;
  agents: Agent[];
}

interface CommunicationFormData {
  name: string;
  description?: string;
  configuration: Record<string, any>;
  agent_ids: number[];
}

export default function CommunicationComponent() {
  const [communications, setCommunications] = useState<Communication[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingCommunication, setEditingCommunication] = useState<Communication | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedAgents, setSelectedAgents] = useState<number[]>([]);

  const initialFormData: CommunicationFormData = {
    name: '',
    description: '',
    configuration: {},
    agent_ids: [],
  };

  const [formData, setFormData] = useState<CommunicationFormData>(initialFormData);

  useEffect(() => {
    fetchCommunications();
    fetchAgents();
  }, []);

  const fetchCommunications = async () => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/communication`);
      if (!response.ok) throw new Error('Failed to fetch communications');
      const data = await response.json();
      setCommunications(data);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch communications",
        variant: "destructive",
      });
    }
  };

  const fetchAgents = async () => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/agent/get-all`);
      if (!response.ok) throw new Error('Failed to fetch agents');
      const data = await response.json();
      setAgents(data);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch agents",
        variant: "destructive",
      });
    }
  };

  const handleCreateCommunication = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_API_URL}/communication/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      
      if (!response.ok) throw new Error('Failed to create communication');
      
      await fetchCommunications();
      setFormData(initialFormData);
      setSelectedAgents([]);
      toast({
        title: "Success",
        description: "Communication created successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create communication",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateCommunication = async (communication: Communication) => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/communication/${communication.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: communication.name,
          description: communication.description,
          configuration: communication.configuration,
          agent_ids: communication.agents.map(agent => agent.id),
        }),
      });
      
      if (!response.ok) throw new Error('Failed to update communication');
      
      await fetchCommunications();
      setIsEditDialogOpen(false);
      setEditingCommunication(null);
      toast({
        title: "Success",
        description: "Communication updated successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update communication",
        variant: "destructive",
      });
    }
  };

  const handleDeleteCommunication = async (communicationId: number) => {
    if (!confirm('Are you sure you want to delete this communication?')) return;
    
    try {
      const response = await fetch(`${BACKEND_API_URL}/communication/${communicationId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) throw new Error('Failed to delete communication');
      
      await fetchCommunications();
      toast({
        title: "Success",
        description: "Communication deleted successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete communication",
        variant: "destructive",
      });
    }
  };

  const handleAgentSelectionChange = (agentId: string) => {
    const numericId = parseInt(agentId);
    const currentAgents = [...formData.agent_ids];
    const index = currentAgents.indexOf(numericId);
    
    if (index === -1) {
      currentAgents.push(numericId);
    } else {
      currentAgents.splice(index, 1);
    }
    
    setFormData({
      ...formData,
      agent_ids: currentAgents,
    });
  };

  const handleCreateConversation = async (communicationId: number) => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/communication/conversations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          communication_id: communicationId,
          title: `Communication ${communicationId} Conversation`,
        }),
      });
      
      if (!response.ok) throw new Error('Failed to create conversation');
      
      toast({
        title: "Success",
        description: "Conversation created successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create conversation",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-1 p-6">
          <h2 className="text-xl font-bold mb-4">Create New Communication</h2>
          <form onSubmit={handleCreateCommunication} className="space-y-4">
            <Input
              placeholder="Communication Name"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
            
            <Textarea
              placeholder="Description"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
            />

            <div className="space-y-2">
              <label className="text-sm font-medium">Select Agents:</label>
              {agents.map((agent) => (
                <div key={agent.id} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id={`agent-${agent.id}`}
                    checked={formData.agent_ids.includes(agent.id)}
                    onChange={() => handleAgentSelectionChange(agent.id.toString())}
                    className="rounded border-gray-300"
                  />
                  <label htmlFor={`agent-${agent.id}`}>{agent.name}</label>
                </div>
              ))}
            </div>
            
            <Button type="submit" disabled={loading} className="w-full">
              <Plus className="w-4 h-4 mr-2" />
              Create Communication
            </Button>
          </form>
        </Card>

        <div className="md:col-span-2">
          <h2 className="text-2xl font-bold mb-4">Communications</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {communications.map((communication) => (
              <Card key={communication.id} className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold">{communication.name}</h3>
                    <p className="text-sm text-gray-600">{communication.description}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleCreateConversation(communication.id)}
                    >
                      <MessageCircle className="w-4 h-4" />
                    </Button>
                    <Dialog open={isEditDialogOpen && editingCommunication?.id === communication.id}>
                      <DialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setEditingCommunication(communication);
                            setIsEditDialogOpen(true);
                          }}
                        >
                          <Settings2 className="w-4 h-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Edit Communication</DialogTitle>
                        </DialogHeader>
                        {editingCommunication && (
                          <div className="space-y-4">
                            <Input
                              placeholder="Communication Name"
                              value={editingCommunication.name}
                              onChange={(e) => setEditingCommunication({
                                ...editingCommunication,
                                name: e.target.value
                              })}
                            />
                            <Textarea
                              placeholder="Description"
                              value={editingCommunication.description}
                              onChange={(e) => setEditingCommunication({
                                ...editingCommunication,
                                description: e.target.value
                              })}
                            />
                            <div className="space-y-2">
                              <label className="text-sm font-medium">Select Agents:</label>
                              {agents.map((agent) => (
                                <div key={agent.id} className="flex items-center space-x-2">
                                  <input
                                    type="checkbox"
                                    id={`edit-agent-${agent.id}`}
                                    checked={editingCommunication.agents.some(a => a.id === agent.id)}
                                    onChange={() => {
                                      const updatedAgents = editingCommunication.agents.some(a => a.id === agent.id)
                                        ? editingCommunication.agents.filter(a => a.id !== agent.id)
                                        : [...editingCommunication.agents, agent];
                                      setEditingCommunication({
                                        ...editingCommunication,
                                        agents: updatedAgents
                                      });
                                    }}
                                    className="rounded border-gray-300"
                                  />
                                  <label htmlFor={`edit-agent-${agent.id}`}>{agent.name}</label>
                                </div>
                              ))}
                            </div>
                            <div className="flex justify-end gap-2">
                              <Button
                                variant="outline"
                                onClick={() => {
                                  setIsEditDialogOpen(false);
                                  setEditingCommunication(null);
                                }}
                              >
                                Cancel
                              </Button>
                              <Button
                                onClick={() => handleUpdateCommunication(editingCommunication)}
                              >
                                <Save className="w-4 h-4 mr-2" />
                                Save Changes
                              </Button>
                            </div>
                          </div>
                        )}
                      </DialogContent>
                    </Dialog>
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={() => handleDeleteCommunication(communication.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <div className="mt-4">
                  <h4 className="text-sm font-medium mb-2">Participating Agents:</h4>
                  <div className="flex flex-wrap gap-2">
                    {communication.agents.map((agent) => (
                      <span
                        key={agent.id}
                        className="bg-gray-100 rounded-full px-3 py-1 text-sm"
                      >
                        {agent.name}
                      </span>
                    ))}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}