import React from 'react';
import PropTypes from 'prop-types';
import './ScenarioSelector.css';

/**
 * Scenario type definitions with icons and descriptions
 */
const SCENARIOS = [
  {
    type: 'student',
    label: 'Student',
    icon: '🎓',
    description: 'College or university students'
  },
  {
    type: 'senior_citizen',
    label: 'Senior Citizen',
    icon: '👴',
    description: 'Elderly individuals (65+ years)'
  },
  {
    type: 'small_business_owner',
    label: 'Small Business Owner',
    icon: '💼',
    description: 'Entrepreneurs and small business operators'
  },
  {
    type: 'parent',
    label: 'Parent',
    icon: '👨‍👩‍👧‍👦',
    description: 'Parents with dependent children'
  },
  {
    type: 'low_income',
    label: 'Low-Income Individual',
    icon: '💰',
    description: 'Individuals below certain income thresholds'
  },
  {
    type: 'veteran',
    label: 'Veteran',
    icon: '🎖️',
    description: 'Military veterans'
  },
  {
    type: 'disabled',
    label: 'Disabled Person',
    icon: '♿',
    description: 'Individuals with disabilities'
  },
  {
    type: 'first_time_homebuyer',
    label: 'First-Time Homebuyer',
    icon: '🏠',
    description: 'People looking to purchase their first home'
  },
  {
    type: 'unemployed',
    label: 'Unemployed',
    icon: '🔍',
    description: 'Job seekers and unemployed individuals'
  },
  {
    type: 'general_citizen',
    label: 'General Citizen',
    icon: '👤',
    description: 'General public'
  }
];

/**
 * ScenarioSelector Component
 * Allows users to select their scenario type and provide additional details
 */
const ScenarioSelector = ({
  selectedScenario,
  onScenarioChange,
  scenarioDetails,
  onDetailsChange,
  disabled = false
}) => {
  return (
    <div className="scenario-selector">
      <div className="scenario-header">
        <h3>Select Your Scenario</h3>
        <p className="scenario-subtitle">
          Choose the option that best describes your situation to get personalized guidance
        </p>
      </div>

      <div className="scenario-grid">
        {SCENARIOS.map((scenario) => (
          <button
            key={scenario.type}
            className={`scenario-card ${selectedScenario === scenario.type ? 'selected' : ''}`}
            onClick={() => onScenarioChange(scenario.type)}
            disabled={disabled}
            title={scenario.description}
          >
            <div className="scenario-icon">{scenario.icon}</div>
            <div className="scenario-label">{scenario.label}</div>
          </button>
        ))}
      </div>

      {selectedScenario && (
        <div className="scenario-details">
          <label htmlFor="scenario-details-input">
            Additional Details (Optional)
          </label>
          <textarea
            id="scenario-details-input"
            className="scenario-details-input"
            value={scenarioDetails}
            onChange={(e) => onDetailsChange(e.target.value)}
            placeholder={`Add more context about your situation (e.g., age, income level, specific circumstances)...`}
            rows={3}
            maxLength={1000}
            disabled={disabled}
          />
          <div className="character-count">
            {scenarioDetails.length}/1000 characters
          </div>
        </div>
      )}
    </div>
  );
};

ScenarioSelector.propTypes = {
  selectedScenario: PropTypes.string,
  onScenarioChange: PropTypes.func.isRequired,
  scenarioDetails: PropTypes.string,
  onDetailsChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool
};

export default ScenarioSelector;
