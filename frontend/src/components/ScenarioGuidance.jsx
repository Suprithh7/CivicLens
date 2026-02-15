import React, { useState } from 'react';
import PropTypes from 'prop-types';
import ScenarioSelector from './ScenarioSelector';
import ScenarioExplanation from './ScenarioExplanation';
import { getScenarioExplanation } from '../services/simplificationService';
import './ScenarioGuidance.css';

/**
 * ScenarioGuidance Component
 * Provides scenario-based policy explanations
 */
const ScenarioGuidance = ({ policyId, policyTitle }) => {
  const [selectedScenario, setSelectedScenario] = useState('');
  const [scenarioDetails, setScenarioDetails] = useState('');
  const [explanation, setExplanation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGetExplanation = async () => {
    if (!selectedScenario) {
      setError('Please select a scenario first');
      return;
    }

    setIsLoading(true);
    setError(null);
    setExplanation(null);

    try {
      const result = await getScenarioExplanation(
        policyId,
        selectedScenario,
        scenarioDetails || null
      );
      setExplanation(result);
    } catch (err) {
      setError(err.message || 'Failed to get scenario explanation');
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedScenario('');
    setScenarioDetails('');
    setExplanation(null);
    setError(null);
  };

  return (
    <div className="scenario-guidance">
      <div className="guidance-header">
        <h2>📖 Scenario-Based Guidance</h2>
        <p className="guidance-subtitle">
          Get personalized explanations based on your specific situation
        </p>
      </div>

      <ScenarioSelector
        selectedScenario={selectedScenario}
        onScenarioChange={setSelectedScenario}
        scenarioDetails={scenarioDetails}
        onDetailsChange={setScenarioDetails}
        disabled={isLoading}
      />

      <div className="guidance-actions">
        <button
          className="get-explanation-btn"
          onClick={handleGetExplanation}
          disabled={!selectedScenario || isLoading}
        >
          {isLoading ? (
            <>
              <span className="spinner">⏳</span> Generating Explanation...
            </>
          ) : (
            <>
              <span>🚀</span> Get Personalized Explanation
            </>
          )}
        </button>

        {(explanation || error) && (
          <button
            className="reset-btn"
            onClick={handleReset}
            disabled={isLoading}
          >
            🔄 Start Over
          </button>
        )}
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {explanation && (
        <ScenarioExplanation
          explanation={explanation.simplified_text}
          scenarioType={selectedScenario}
          policyTitle={explanation.policy_title || policyTitle}
        />
      )}
    </div>
  );
};

ScenarioGuidance.propTypes = {
  policyId: PropTypes.string.isRequired,
  policyTitle: PropTypes.string
};

export default ScenarioGuidance;
