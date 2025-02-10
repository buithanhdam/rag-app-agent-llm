'use client';

import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';
interface Foundation {
    id: string;
    model_name: string;
    model_id:string;
    provider: string;
    description: string;
  }
  
  interface Config {
    id: string;
    name: string;
    temperature: number;
    max_tokens: number;
    system_prompt: string;
  }
export default function LLMPage() {
    const [activeTab, setActiveTab] = useState<string>('foundations');
    const [foundations, setFoundations] = useState<Foundation[]>([
      {
        id: '1',
        model_name: 'Sample Model 1',
        model_id:"gpt-3.5",
        provider: 'OpenAI',
        description: 'Sample description for Model 1',

      },
    ]);
    const [configs, setConfigs] = useState<Config[]>([]);
    const [selectedFoundation, setSelectedFoundation] = useState<string>('');
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string>('');
  
    const [newConfig, setNewConfig] = useState<Config>({
      id: '',
      name: '',
      temperature: 0.7,
      max_tokens: 1000,
      system_prompt: '',
    });

  useEffect(() => {
    fetchFoundations();
  }, []);

  const fetchFoundations = async () => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/llm/foundations/get`);
      if (!response.ok) throw new Error('Failed to fetch foundations');
      const data = await response.json();
      setFoundations(data);
    } catch (error) {
      setError('Failed to load LLM foundations');
      console.error('Error:', error);
    }
  };

  const fetchConfigsByFoundation = async (foundationId:string) => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/llm/foundations/${foundationId}/configs`);
      if (!response.ok) throw new Error('Failed to fetch configs');
      const data = await response.json();
      setConfigs(data);
    } catch (error) {
      setError('Failed to load configurations');
      console.error('Error:', error);
    }
  };

  const handleFoundationSelect = (foundationId:string) => {
    setSelectedFoundation(foundationId);
    fetchConfigsByFoundation(foundationId);
  };

  const handleCreateConfig = async (e:any) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${BACKEND_API_URL}/llm/configs/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newConfig,
          foundation_id: selectedFoundation
        }),
      });
      if (!response.ok) throw new Error('Failed to create configuration');
      
      fetchConfigsByFoundation(selectedFoundation);
      setNewConfig({
        name: '',
        temperature: 0.7,
        max_tokens: 1000,
        system_prompt: '',
        id: ''
      });
    } catch (error) {
      setError('Failed to create configuration');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4">
      {error && (
        <div className="bg-red-100 text-red-700 p-2 mb-4 rounded">
          {error}
        </div>
      )}

      <div className="flex gap-2 mb-4">
        <Button
          variant={activeTab === 'foundations' ? 'default' : 'outline'}
          onClick={() => setActiveTab('foundations')}
        >
          Foundations
        </Button>
        <Button
          variant={activeTab === 'configs' ? 'default' : 'outline'}
          onClick={() => setActiveTab('configs')}
        >
          Configurations
        </Button>
      </div>

      {activeTab === 'foundations' ? (
        <Card className="p-6">
          <h2 className="text-2xl font-bold mb-4">LLM Foundations</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {foundations.map((foundation) => (
              <Card key={foundation.id} className="p-4">
                <h3 className="font-semibold">{foundation.model_name}</h3>
                <p className="text-sm text-gray-600">{foundation.provider}</p>
                <p className="text-sm text-gray-600">{foundation.model_id}</p>
                <p className="text-sm mt-2">{foundation.description}</p>
                <Button 
                  className="mt-4"
                  onClick={() => handleFoundationSelect(foundation.id)}
                >
                  View Configs
                </Button>
              </Card>
            ))}
          </div>
        </Card>
      ) : (
        <Card className="p-6">
  <h2 className="text-2xl font-bold mb-4">LLM Configurations</h2>
  {selectedFoundation ? (
    <div className="space-y-6">
      <form onSubmit={handleCreateConfig} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Configuration Name</label>
          <Input
            placeholder="Configuration Name"
            value={newConfig.name}
            onChange={(e) => setNewConfig({...newConfig, name: e.target.value})}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Temperature (0.1 - 1.0)</label>
            <Input
              type="number"
              step="0.1"
              min="0.1"
              max="1.0"
              placeholder="Temperature"
              value={newConfig.temperature}
              onChange={(e) => {
                const temp = parseFloat(e.target.value);
                if (temp >= 0.1 && temp <= 1.0) {
                  setNewConfig({...newConfig, temperature: temp});
                }
              }}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Max Tokens (1000 - 4000)</label>
            <Input
              type="number"
              min="1000"
              max="4000"
              placeholder="Max Tokens"
              value={newConfig.max_tokens}
              onChange={(e) => {
                const tokens = parseInt(e.target.value, 10);
                if (tokens >= 1000 && tokens <= 4000) {
                  setNewConfig({...newConfig, max_tokens: tokens});
                }
              }}
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">System Prompt</label>
          <Textarea
            placeholder="System Prompt"
            value={newConfig.system_prompt}
            onChange={(e) => setNewConfig({...newConfig, system_prompt: e.target.value})}
          />
        </div>
        <Button type="submit" disabled={loading}>
          Create Configuration
        </Button>
      </form>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        {configs.map((config) => (
          <Card key={config.id} className="p-4">
            <h3 className="font-semibold">{config.name}</h3>
            <div className="mt-2 space-y-2 text-sm">
              <p>Temperature: {config.temperature}</p>
              <p>Max Tokens: {config.max_tokens}</p>
              <p className="truncate">System Prompt: {config.system_prompt}</p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  ) : (
    <p>Please select a foundation first</p>
  )}
</Card>

      )}
    </div>
  );
}