/**
 * API utility functions
 * Helpers for API requests and error handling
 */

/**
 * Build query string from parameters object
 * @param {Object} params - Parameters object
 * @returns {string} Query string (without leading ?)
 */
export function buildQueryString(params) {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      searchParams.append(key, value.toString());
    }
  });

  return searchParams.toString();
}

/**
 * Handle API error and return user-friendly message
 * @param {Error} error - Error object
 * @returns {string} User-friendly error message
 */
export function handleApiError(error) {
  if (error.message) {
    return error.message;
  }

  if (error.response) {
    // Server responded with error status
    return error.response.data?.detail || error.response.data?.message || 'Server error occurred';
  }

  if (error.request) {
    // Request was made but no response received
    return 'Network error. Please check your connection';
  }

  return 'An unexpected error occurred';
}

/**
 * Check if error is a network error
 * @param {Error} error - Error object
 * @returns {boolean} True if network error
 */
export function isNetworkError(error) {
  return error.request && !error.response;
}

/**
 * Check if error is a server error (5xx)
 * @param {Error} error - Error object
 * @returns {boolean} True if server error
 */
export function isServerError(error) {
  return error.response && error.response.status >= 500;
}

/**
 * Check if error is a client error (4xx)
 * @param {Error} error - Error object
 * @returns {boolean} True if client error
 */
export function isClientError(error) {
  return error.response && error.response.status >= 400 && error.response.status < 500;
}
