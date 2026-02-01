/**
 * API Service
 * Centralized API communication layer for the CivicLens frontend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const config = { ...defaultOptions, ...options };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
}

/**
 * Health check endpoint
 */
export async function checkHealth() {
  return fetchAPI('/api/v1/health');
}

/**
 * Get root API information
 */
export async function getRootInfo() {
  return fetchAPI('/');
}

/**
 * Upload a policy document
 */
export async function uploadPolicy(file) {
  const formData = new FormData();
  formData.append('file', file);

  const url = `${API_BASE_URL}/api/v1/policies/upload`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API Error (upload policy):', error);
    throw error;
  }
}

/**
 * List policies with optional filters and pagination
 */
export async function listPolicies({
  status = null,
  policyType = null,
  jurisdiction = null,
  limit = 20,
  offset = 0,
} = {}) {
  const params = new URLSearchParams();

  if (status) params.append('status', status);
  if (policyType) params.append('policy_type', policyType);
  if (jurisdiction) params.append('jurisdiction', jurisdiction);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  const queryString = params.toString();
  const endpoint = `/api/v1/policies/list${queryString ? `?${queryString}` : ''}`;

  return fetchAPI(endpoint);
}

/**
 * Get a single policy by ID
 */
export async function getPolicyById(policyId) {
  return fetchAPI(`/api/v1/policies/${policyId}`);
}

/**
 * Delete a policy by ID
 */
export async function deletePolicy(policyId) {
  const url = `${API_BASE_URL}/api/v1/policies/${policyId}`;

  try {
    const response = await fetch(url, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return true;
  } catch (error) {
    console.error(`API Error (delete policy ${policyId}):`, error);
    throw error;
  }
}

export default {
  checkHealth,
  getRootInfo,
  uploadPolicy,
  listPolicies,
  getPolicyById,
  deletePolicy,
};
