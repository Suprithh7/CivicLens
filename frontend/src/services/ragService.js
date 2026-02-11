/**
 * RAG Service
 * API functions for RAG (Retrieval-Augmented Generation) question answering
 */

import { API_BASE_URL } from '../constants';

/**
 * Ask a question about policy documents (non-streaming)
 * @param {Object} params - Query parameters
 * @param {string} params.query - The question to ask
 * @param {string} [params.policyId] - Optional policy ID to limit search scope
 * @param {number} [params.topK=5] - Number of chunks to retrieve
 * @param {number} [params.temperature] - LLM temperature
 * @param {string} [params.model] - LLM model to use
 * @returns {Promise<Object>} RAG response with answer and sources
 */
export async function askQuestion({ query, policyId = null, topK = 5, temperature = null, model = null }) {
  const url = `${API_BASE_URL}/api/v1/rag/ask`;

  const requestBody = {
    query,
    top_k: topK,
  };

  if (policyId) requestBody.policy_id = policyId;
  if (temperature !== null) requestBody.temperature = temperature;
  if (model) requestBody.model = model;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail?.message || errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API Error (ask question):', error);
    throw error;
  }
}

/**
 * Ask a question with streaming response
 * @param {Object} params - Query parameters
 * @param {string} params.query - The question to ask
 * @param {string} [params.policyId] - Optional policy ID to limit search scope
 * @param {number} [params.topK=5] - Number of chunks to retrieve
 * @param {number} [params.temperature] - LLM temperature
 * @param {string} [params.model] - LLM model to use
 * @param {Function} onChunk - Callback for each chunk received
 * @param {Function} onError - Callback for errors
 * @returns {Promise<void>}
 */
export async function askQuestionStreaming({
  query,
  policyId = null,
  topK = 5,
  temperature = null,
  model = null,
  onChunk,
  onError
}) {
  const url = `${API_BASE_URL}/api/v1/rag/ask-stream`;

  const requestBody = {
    query,
    top_k: topK,
  };

  if (policyId) requestBody.policy_id = policyId;
  if (temperature !== null) requestBody.temperature = temperature;
  if (model) requestBody.model = model;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail?.message || errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete lines (NDJSON format)
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.trim()) {
          try {
            const chunk = JSON.parse(line);

            if (chunk.type === 'error') {
              if (onError) onError(new Error(chunk.error));
              return;
            }

            if (onChunk) onChunk(chunk);
          } catch (e) {
            console.error('Error parsing chunk:', e);
          }
        }
      }
    }
  } catch (error) {
    console.error('API Error (ask question streaming):', error);
    if (onError) onError(error);
    throw error;
  }
}

/**
 * Check RAG service health
 * @returns {Promise<Object>} Health status
 */
export async function checkRAGHealth() {
  const url = `${API_BASE_URL}/api/v1/rag/health`;

  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API Error (RAG health check):', error);
    throw error;
  }
}

export default {
  askQuestion,
  askQuestionStreaming,
  checkRAGHealth,
};
