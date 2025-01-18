'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { Upload, FileText, Search } from 'lucide-react';

export default function DocumentComponent() {
  const [file, setFile] = useState<File | null>(null);
  const [collectionName, setCollectionName] = useState('documents');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingResult, setProcessingResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a PDF file');
      setFile(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploadProgress(0);
      const response = await fetch(
        `http://localhost:8000/kb/upload?collection_name=${collectionName}`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) throw new Error('Upload failed');

      const result = await response.json();
      setProcessingResult(result);
      setUploadProgress(100);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Upload failed');
      setUploadProgress(0);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-6">
          <FileText className="w-6 h-6" />
          <h2 className="text-xl font-semibold">Document Processing</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Collection Name
            </label>
            <Input
              value={collectionName}
              onChange={(e) => setCollectionName(e.target.value)}
              placeholder="Enter collection name"
              className="max-w-xs"
            />
          </div>

          <div className="border-2 border-dashed rounded-lg p-6 text-center">
            <input
              type="file"
              onChange={handleFileChange}
              accept=".pdf"
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer flex flex-col items-center"
            >
              <Upload className="w-12 h-12 text-gray-400 mb-2" />
              <span className="text-sm text-gray-600">
                {file ? file.name : 'Click to upload PDF file'}
              </span>
            </label>
          </div>

          {uploadProgress > 0 && (
            <Progress value={uploadProgress} className="w-full" />
          )}

          {error && (
            <div className="text-red-500 text-sm mt-2">{error}</div>
          )}

          <Button
            onClick={handleUpload}
            disabled={!file}
            className="w-full"
          >
            Process Document
          </Button>

          {processingResult && (
            <div className="mt-4">
              <h3 className="font-semibold mb-2">Processing Result:</h3>
              <pre className="bg-gray-100 p-4 rounded-lg overflow-x-auto">
                {JSON.stringify(processingResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}