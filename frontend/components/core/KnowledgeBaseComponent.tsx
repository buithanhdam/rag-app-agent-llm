'use client';
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Upload, FileText, Search, Plus, Database } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';
interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  created_at: string;
}

interface Document {
  id: string;
  name: string;
  extension: string;
  status: string;
  created_at: string;
  content_type: string;
}

interface NewKBData {
  name: string;
  description: string;
  rag_type: string;
  embedding_model: string;
  similarity_type: string;
  chunk_size: number;
  chunk_overlap: number;
}
const KnowledgeBaseComponent: React.FC = () => {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKB, setSelectedKB] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  // Form states for creating new KB
  const [newKBData, setNewKBData] = useState<NewKBData>({
    name: '',
    description: '',
    rag_type: 'normal_rag',
    embedding_model: 'models/embedding-001',
    similarity_type: 'cosine',
    chunk_size: 512,
    chunk_overlap: 64
  });

  useEffect(() => {
    fetchKnowledgeBases();
  }, []);

  const fetchKnowledgeBases = async () => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/kb/`);
      const data: KnowledgeBase[] = await response.json();
      setKnowledgeBases(data);
    } catch (error) {
      setError('Failed to fetch knowledge bases');
    }
  };

  const fetchDocuments = async (kbId: string) => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/kb/${kbId}/documents`);
      const data: Document[] = await response.json();
      setDocuments(data);
    } catch (error) {
      setError('Failed to fetch documents');
    }
  };

  const handleCreateKB = async () => {
    try {
      const response = await fetch(`${BACKEND_API_URL}/kb/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newKBData)
      });

      if (!response.ok) throw new Error('Failed to create knowledge base');

      await fetchKnowledgeBases();
      return true;
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
      return false;
    }
  };

  const handleFileUpload = async () => {
    if (!file || !selectedKB) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_data', JSON.stringify({
      knowledge_base_id: selectedKB.id,
      name: file.name,
      extension: file.type
    }));

    try {
      setUploadProgress(0);
      const response = await fetch(
        `${BACKEND_API_URL}/kb/${selectedKB.id}/documents`,
        {
          method: 'POST',
          body: formData
        }
      );

      if (!response.ok) throw new Error('Upload failed');

      setUploadProgress(100);
      await fetchDocuments(selectedKB.id);
      setFile(null);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Upload failed');
      setUploadProgress(0);
    }
  };

  return (
    <div className="container mx-auto p-4 space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Knowledge Base Management</CardTitle>
          <Dialog>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Knowledge Base
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Knowledge Base</DialogTitle>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <Input
                  placeholder="Name"
                  value={newKBData.name}
                  onChange={(e) => setNewKBData({ ...newKBData, name: e.target.value })}
                />
                <Input
                  placeholder="Description"
                  value={newKBData.description}
                  onChange={(e) => setNewKBData({ ...newKBData, description: e.target.value })}
                />
                <Select
                  value={newKBData.rag_type}
                  onValueChange={(value) => setNewKBData({ ...newKBData, rag_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="RAG Type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="normal_rag">Normal</SelectItem>
                    <SelectItem value="hybrid_rag">Hybrid</SelectItem>
                    <SelectItem value="contextual_rag">Contextual</SelectItem>
                    <SelectItem value="fusion_rag">Fusion</SelectItem>
                    <SelectItem value="hyde_rag">HyDE</SelectItem>
                    <SelectItem value="naive_rag">Naive</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  type="number"
                  placeholder="Chunk Size"
                  value={newKBData.chunk_size}
                  onChange={(e) => setNewKBData({ ...newKBData, chunk_size: parseInt(e.target.value) })}
                />
                <Input
                  type="number"
                  placeholder="Chunk Overlap"
                  value={newKBData.chunk_overlap}
                  onChange={(e) => setNewKBData({ ...newKBData, chunk_overlap: parseInt(e.target.value) })}
                />
                <Button onClick={handleCreateKB}>Create</Button>
              </div>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="knowledge-bases">
            <TabsList>
              <TabsTrigger value="knowledge-bases">Knowledge Bases</TabsTrigger>
              <TabsTrigger value="documents" disabled={!selectedKB}>Documents</TabsTrigger>
            </TabsList>

            <TabsContent value="knowledge-bases">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {knowledgeBases.map((kb) => (
                  <Card
                    key={kb.id}
                    className={`cursor-pointer ${selectedKB?.id === kb.id ? 'border-primary' : ''}`}
                    onClick={() => {
                      setSelectedKB(kb);
                      fetchDocuments(kb.id);
                    }}
                  >
                    <CardHeader>
                      <CardTitle className="text-lg">{kb.name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-500">{kb.description}</p>
                      <p className="text-sm mt-2">Created: {new Date(kb.created_at).toLocaleDateString()}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="documents">
              {selectedKB && (
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <Input
                      type="file"
                      accept=".pdf,.txt,.doc,.docx"
                      onChange={(e) => setFile(e.target.files?.[0] || null)}
                      className="max-w-xs"
                    />
                    <Button onClick={handleFileUpload} disabled={!file}>
                      <Upload className="mr-2 h-4 w-4" />
                      Upload Document
                    </Button>
                  </div>

                  {uploadProgress > 0 && (
                    <Progress value={uploadProgress} className="w-full" />
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {documents.map((doc) => (
                      <Card key={doc.id}>
                        <CardHeader>
                          <CardTitle className="text-lg">{doc.name}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-sm text-gray-500">Type: {doc.extension}</p>
                          <p className="text-sm text-gray-500">Status: {doc.status}</p>
                          <p className="text-sm">Created: {new Date(doc.created_at).toLocaleDateString()}</p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
    </div>
  );
};

export default KnowledgeBaseComponent;