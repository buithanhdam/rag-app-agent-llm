'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Plus, Settings2, Trash2 } from 'lucide-react';

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';
type Agent = {
    id:string,
    name: string;
    agent_type: string;
    description: string;
    configuration: {};
    tools: []
  };
export default function AgentComponent() {

  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [newAgent, setNewAgent] = useState<Agent>({
    id:'',
    name: '',
    agent_type: '',
    description: '',
    configuration: {},
    tools: []
  });

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/agent/get-all`);
      const data = await response.json();
      setAgents(data);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  };

  const handleCreateAgent = async (e:any) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_API_URL}/agent/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newAgent),
      });
      if (response.ok) {
        fetchAgents();
        setNewAgent({
            id:'',
          name: '',
          agent_type: '',
          description: '',
          configuration: {},
          tools: []
        });
      }
    } catch (error) {
      console.error('Error creating agent:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAgent = async (agentId:string) => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/agent/delete/${agentId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        fetchAgents();
      }
    } catch (error) {
      console.error('Error deleting agent:', error);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-1 p-6">
          <h2 className="text-xl font-bold mb-4">Create New Agent</h2>
          <form onSubmit={handleCreateAgent} className="space-y-4">
            <Input
              placeholder="Agent Name"
              value={newAgent.name}
              onChange={(e) => setNewAgent({...newAgent, name: e.target.value})}
            />
            <Input
              placeholder="Agent Type"
              value={newAgent.agent_type}
              onChange={(e) => setNewAgent({...newAgent, agent_type: e.target.value})}
            />
            <Textarea
              placeholder="Description"
              value={newAgent.description}
              onChange={(e) => setNewAgent({...newAgent, description: e.target.value})}
            />
            <Button type="submit" disabled={loading} className="w-full">
              <Plus className="w-4 h-4 mr-2" />
              Create Agent
            </Button>
          </form>
        </Card>

        <div className="md:col-span-2">
          <h2 className="text-2xl font-bold mb-4">Agents</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {agents.map((agent) => (
              <Card key={agent.id} className="p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold">{agent.name}</h3>
                    <p className="text-sm text-gray-600">{agent.agent_type}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Settings2 className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={() => handleDeleteAgent(agent.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <p className="text-sm mt-2">{agent.description}</p>
                <div className="mt-2">
                  {agent.tools && agent.tools.map((tool, index) => (
                    <span 
                      key={index}
                      className="inline-block bg-gray-100 rounded-full px-3 py-1 text-sm mr-2 mt-2"
                    >
                      {tool}
                    </span>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}