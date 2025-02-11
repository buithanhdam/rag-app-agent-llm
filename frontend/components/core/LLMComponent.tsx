'use client';
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';

interface Foundation {
  id: number;
  provider: string;
  model_name: string;
  model_id: string;
  description?: string;
  capabilities?: {};
}

interface Config{
    id:number;
    foundation_id: number;
    name: string;
    temperature: number;
    max_tokens: number;
    top_p?: number;
    frequency_penalty?: number;
    presence_penalty?: number;
    system_prompt: string;
    stop_sequences?: [];
}

const defaultFoundation: Foundation = {
  id:0,
  provider: '',
  model_name: '',
  model_id: '',
  description: '',
  capabilities: {}
}

const defaultConfig: Config = {
  id:0,
  foundation_id: 0,
  name: '',
  temperature: 0.7,
  max_tokens: 100,
  top_p: 1,
  frequency_penalty: 0,
  presence_penalty: 0,
  system_prompt: '',
  stop_sequences: []
}

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';

const LLMComponent = () => {
  const [foundations, setFoundations] = useState<Foundation[]>([]);
  const [selectedFoundation, setSelectedFoundation] = useState<Foundation>(defaultFoundation);
  const [configs, setConfigs] = useState<Config[]>([]);
  const [showFoundationForm, setShowFoundationForm] = useState(false);
  const [showConfigForm, setShowConfigForm] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  // Foundation form state
  const [foundationForm, setFoundationForm] = useState<Foundation>(defaultFoundation);

  // Config form state
  const [configForm, setConfigForm] = useState<Config>(defaultConfig);

  // Fetch foundations
  const fetchFoundations = async () => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/llm/foundations/get`);
      const data = await response.json();
      setFoundations(data);
    } catch (error) {
      console.error('Error fetching foundations:', error);
    }
  };

  // Fetch configs for a foundation
  const fetchConfigs = async (foundationId: number) => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/llm/foundations/${foundationId}/configs`);
      const data = await response.json();
      setConfigs(data);
    } catch (error) {
      console.error('Error fetching configs:', error);
    }
  };

  // Create foundation
  const handleCreateFoundation = async () => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/llm/foundations/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(foundationForm)
      });
      if (response.ok) {
        setShowFoundationForm(false);
        setFoundationForm(defaultFoundation);
        fetchFoundations();
      }
    } catch (error) {
      console.error('Error creating foundation:', error);
    }
  };

  // Create config
  const handleCreateConfig = async () => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/llm/configs/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...configForm, foundation_id: selectedFoundation.id })
      });
      if (response.ok) {
        setShowConfigForm(false);
        setConfigForm(defaultConfig)
        fetchConfigs(selectedFoundation.id);
      }
    } catch (error) {
      console.error('Error creating config:', error);
    }
  };

  // Delete foundation
  const handleDeleteFoundation = async (id:number) => {
    try {
      await fetch(`${BACKEND_API_URL}/llm/foundations/delete/${id}`, { method: 'DELETE' });
      fetchFoundations();
      setSelectedFoundation(defaultFoundation);
    } catch (error) {
      console.error('Error deleting foundation:', error);
    }
  };

  // Delete config
  const handleDeleteConfig = async (id: number) => {
    try {
      await fetch(`${BACKEND_API_URL}/llm/configs/delete/${id}`, { method: 'DELETE' });
      fetchConfigs(selectedFoundation.id);
    } catch (error) {
      console.error('Error deleting config:', error);
    }
  };

  useEffect(() => {
    fetchFoundations();
  }, []);

  useEffect(() => {
    if (selectedFoundation) {
      fetchConfigs(selectedFoundation.id);
    }
  }, [selectedFoundation]);

  return (
    <div className="p-4 space-y-4">
      <div className="flex justify-between items-center">
        <Dialog open={showFoundationForm} onOpenChange={setShowFoundationForm}>
          <DialogTrigger asChild>
            <Button>Add Foundation</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add LLM Foundation</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <Select
                value={foundationForm.provider}
                onValueChange={(value) => setFoundationForm({ ...foundationForm, provider: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select Provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="gemini">Gemini</SelectItem>
                  <SelectItem value="anthropic">Anthropic</SelectItem>
                </SelectContent>
              </Select>
              <Input
                placeholder="Model Name"
                value={foundationForm.model_name}
                onChange={(e) => setFoundationForm({ ...foundationForm, model_name: e.target.value })}
              />
              <Input
                placeholder="Model ID"
                value={foundationForm.model_id}
                onChange={(e) => setFoundationForm({ ...foundationForm, model_id: e.target.value })}
              />
              <Input
                placeholder="Description"
                value={foundationForm.description}
                onChange={(e) => setFoundationForm({ ...foundationForm, description: e.target.value })}
              />
              <Button onClick={handleCreateFoundation}>Create Foundation</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Foundations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {foundations.map((foundation) => (
                  <div
                    key={foundation.id}
                    className={`p-2 border rounded cursor-pointer ${
                      selectedFoundation?.id === foundation.id ? 'bg-blue-100' : ''
                    }`}
                    onClick={() => setSelectedFoundation(foundation)}
                  >
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="font-medium text-black-600">Provider: {foundation.provider}</div>
                        <div className="text-sm text-red-500">Name: {foundation.model_name}</div>
                        <div className="text-sm text-gray-500">{foundation.model_id}</div>
                      </div>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button variant="destructive" size="sm">Delete</Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete Foundation</AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to delete this foundation? This action cannot be undone.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={() => handleDeleteFoundation(foundation.id)}>
                              Delete
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="col-span-2">
          {selectedFoundation && (
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>Configs for {selectedFoundation.model_name}</CardTitle>
                  <Dialog open={showConfigForm} onOpenChange={setShowConfigForm}>
                    <DialogTrigger asChild>
                      <Button>Add Config</Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Add LLM Config</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <Input
                          placeholder="Name"
                          value={configForm.name}
                          onChange={(e) => setConfigForm({ ...configForm, name: e.target.value })}
                        />
                        <Input
                          type="number"
                          min={0}
                          max={1}
                          step={0.1}
                          placeholder="Temperature"
                          value={configForm.temperature}
                          onChange={(e) => setConfigForm({ ...configForm, temperature: parseFloat(e.target.value) })}
                        />
                        <Input
                          type="number"
                          placeholder="Max Tokens"
                          min={512}
                          step={100}
                          max={5000}
                          value={configForm.max_tokens}
                          onChange={(e) => setConfigForm({ ...configForm, max_tokens: parseInt(e.target.value) })}
                        />
                        <Input
                          placeholder="System Prompt"
                          value={configForm.system_prompt}
                          onChange={(e) => setConfigForm({ ...configForm, system_prompt: e.target.value })}
                        />
                        <Button onClick={handleCreateConfig}>Create Config</Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {configs.map((config) => (
                    <Card key={config.id}>
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="font-medium">{config.name}</h3>
                            <div className="text-sm text-gray-500">
                              Temperature: {config.temperature} | Max Tokens: {config.max_tokens}
                            </div>
                            <div className="mt-2">
                              <div className="text-sm font-medium">System Prompt:</div>
                              <div className="text-sm text-gray-600">{config.system_prompt}</div>
                            </div>
                          </div>
                          <div className="space-x-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setConfigForm(config);
                                setIsEditing(true);
                                setShowConfigForm(true);
                              }}
                            >
                              Edit
                            </Button>
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button variant="destructive" size="sm">Delete</Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Delete Config</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    Are you sure you want to delete this config? This action cannot be undone.
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction onClick={() => handleDeleteConfig(config.id)}>
                                    Delete
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default LLMComponent;