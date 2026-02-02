/**
 * Custom hook for file upload functionality
 * Manages file selection, validation, and upload state
 */

import { useState } from 'react';
import { uploadPolicy } from '../services/api';
import { validateFile } from '../utils/fileUtils';

export function useFileUpload() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];

    // Reset previous states
    setError(null);
    setUploadResult(null);

    if (file) {
      // Validate file
      const validation = validateFile(file);
      if (!validation.valid) {
        setError(validation.error);
        setSelectedFile(null);
        return;
      }

      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const result = await uploadPolicy(selectedFile);
      setUploadResult(result);
      setSelectedFile(null);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setUploading(false);
    }
  };

  const resetUpload = () => {
    setSelectedFile(null);
    setUploadResult(null);
    setError(null);
  };

  return {
    selectedFile,
    uploading,
    uploadResult,
    error,
    handleFileSelect,
    handleUpload,
    resetUpload,
    setSelectedFile,
  };
}
