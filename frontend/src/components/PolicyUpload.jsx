import React from 'react';
import { useFileUpload } from '../hooks/useFileUpload';
import { formatFileSize } from '../utils/fileUtils';
import ErrorMessage from './common/ErrorMessage';
import SuccessMessage from './common/SuccessMessage';
import { MAX_FILE_SIZE_MB } from '../constants';

function PolicyUpload() {
  const {
    selectedFile,
    uploading,
    uploadResult,
    error,
    handleFileSelect,
    handleUpload,
    setSelectedFile,
  } = useFileUpload();

  const resetFileInput = () => {
    document.getElementById('file-input').value = '';
  };

  const onUpload = async () => {
    try {
      await handleUpload();
      resetFileInput();
    } catch (err) {
      // Error is already handled in the hook
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-semibold text-gray-800 mb-4">
        Upload Policy Document
      </h3>

      <div className="space-y-4">
        {/* File Input */}
        <div>
          <label
            htmlFor="file-input"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Select PDF File (Max {MAX_FILE_SIZE_MB}MB)
          </label>
          <input
            id="file-input"
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileSelect}
            disabled={uploading}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-lg file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-50 file:text-blue-700
              hover:file:bg-blue-100
              disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        {/* Selected File Info */}
        {selectedFile && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                  <p className="text-xs text-gray-500">{formatFileSize(selectedFile.size)}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedFile(null)}
                disabled={uploading}
                className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Upload Button */}
        <button
          onClick={onUpload}
          disabled={!selectedFile || uploading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          {uploading ? (
            <>
              <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>Uploading...</span>
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <span>Upload Document</span>
            </>
          )}
        </button>

        {/* Error Message */}
        {error && (
          <ErrorMessage
            title="Upload Failed"
            message={error}
          />
        )}

        {/* Success Message */}
        {uploadResult && (
          <SuccessMessage
            title="Upload Successful!"
            details={
              <>
                <p><span className="font-semibold">ID:</span> {uploadResult.id}</p>
                <p><span className="font-semibold">Filename:</span> {uploadResult.filename}</p>
                <p><span className="font-semibold">Size:</span> {formatFileSize(uploadResult.file_size)}</p>
                <p><span className="font-semibold">Status:</span> {uploadResult.status}</p>
              </>
            }
          />
        )}
      </div>
    </div>
  );
}

export default PolicyUpload;
