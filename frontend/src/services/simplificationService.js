/**
 * API service for policy simplification endpoints
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Explain a policy with various explanation types
 */
export const explainPolicy = async (policyId, options = {}) => {
  const {
    explanationType = 'explanation',
    focusArea = null,
    temperature = null,
    model = null,
    language = null
  } = options;

  const requestBody = {
    policy_id: policyId,
    explanation_type: explanationType
  };

  if (focusArea) requestBody.focus_area = focusArea;
  if (temperature !== null) requestBody.temperature = temperature;
  if (model) requestBody.model = model;
  if (language) requestBody.language = language;

  const response = await fetch(`${API_BASE_URL}/api/v1/simplification/explain`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Failed to explain policy');
  }

  return await response.json();
};

/**
 * Check eligibility for a policy based on user situation
 */
export const checkEligibility = async (policyId, userSituation, options = {}) => {
  const {
    temperature = null,
    model = null,
    language = null
  } = options;

  const requestBody = {
    policy_id: policyId,
    explanation_type: 'eligibility',
    user_situation: userSituation
  };

  if (temperature !== null) requestBody.temperature = temperature;
  if (model) requestBody.model = model;
  if (language) requestBody.language = language;

  const response = await fetch(`${API_BASE_URL}/api/v1/simplification/explain`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Failed to check eligibility');
  }

  return await response.json();
};

/**
 * Get scenario-based explanation for a policy
 */
export const getScenarioExplanation = async (policyId, scenarioType, scenarioDetails = null, options = {}) => {
  const {
    temperature = null,
    model = null,
    language = null
  } = options;

  const requestBody = {
    policy_id: policyId,
    explanation_type: 'scenario',
    scenario_type: scenarioType
  };

  if (scenarioDetails) requestBody.scenario_details = scenarioDetails;
  if (temperature !== null) requestBody.temperature = temperature;
  if (model) requestBody.model = model;
  if (language) requestBody.language = language;

  const response = await fetch(`${API_BASE_URL}/api/v1/simplification/explain`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Failed to get scenario explanation');
  }

  return await response.json();
};

/**
 * Get key points from a policy
 */
export const getKeyPoints = async (policyId, maxPoints = 5, options = {}) => {
  const {
    temperature = null,
    model = null,
    language = null
  } = options;

  const requestBody = {
    policy_id: policyId,
    explanation_type: 'key_points',
    max_points: maxPoints
  };

  if (temperature !== null) requestBody.temperature = temperature;
  if (model) requestBody.model = model;
  if (language) requestBody.language = language;

  const response = await fetch(`${API_BASE_URL}/api/v1/simplification/explain`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Failed to get key points');
  }

  return await response.json();
};

/**
 * Get benefits summary for a policy
 */
export const getBenefits = async (policyId, options = {}) => {
  const {
    temperature = null,
    model = null,
    language = null
  } = options;

  const requestBody = {
    policy_id: policyId,
    explanation_type: 'benefits'
  };

  if (temperature !== null) requestBody.temperature = temperature;
  if (model) requestBody.model = model;
  if (language) requestBody.language = language;

  const response = await fetch(`${API_BASE_URL}/api/v1/simplification/explain`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Failed to get benefits');
  }

  return await response.json();
};

/**
 * Get application process for a policy
 */
export const getApplicationProcess = async (policyId, options = {}) => {
  const {
    temperature = null,
    model = null,
    language = null
  } = options;

  const requestBody = {
    policy_id: policyId,
    explanation_type: 'application'
  };

  if (temperature !== null) requestBody.temperature = temperature;
  if (model) requestBody.model = model;
  if (language) requestBody.language = language;

  const response = await fetch(`${API_BASE_URL}/api/v1/simplification/explain`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Failed to get application process');
  }

  return await response.json();
};
