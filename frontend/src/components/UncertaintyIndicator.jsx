import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './UncertaintyIndicator.css';

/**
 * UncertaintyIndicator Component
 * Displays AI confidence level and uncertainty information
 */
const UncertaintyIndicator = ({
  confidenceLevel = 'high',
  missingInformation = null,
  isPartialAnswer = false,
  suggestions = null
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Don't show indicator for high confidence with no issues
  if (confidenceLevel === 'high' && !isPartialAnswer && !missingInformation && !suggestions) {
    return null;
  }

  const getConfidenceConfig = (level) => {
    switch (level) {
      case 'low':
      case 'uncertain':
        return {
          label: 'Low Confidence',
          icon: '⚠️',
          color: '#f44336',
          bgColor: '#ffebee',
          message: 'I have limited information and cannot provide a complete answer.'
        };
      case 'medium':
        return {
          label: 'Medium Confidence',
          icon: 'ℹ️',
          color: '#ff9800',
          bgColor: '#fff3e0',
          message: 'I can provide some guidance, but additional information would help.'
        };
      case 'high':
      default:
        return {
          label: 'High Confidence',
          icon: '✓',
          color: '#4caf50',
          bgColor: '#f1f8f4',
          message: 'I have sufficient information to provide accurate guidance.'
        };
    }
  };

  const config = getConfidenceConfig(confidenceLevel);

  return (
    <div className="uncertainty-indicator" style={{ borderLeftColor: config.color }}>
      <div className="uncertainty-header">
        <div className="confidence-badge" style={{ backgroundColor: config.bgColor, color: config.color }}>
          <span className="confidence-icon">{config.icon}</span>
          <span className="confidence-label">{config.label}</span>
        </div>

        {(missingInformation || suggestions) && (
          <button
            className="expand-btn"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
          >
            {isExpanded ? '▼' : '▶'} {isExpanded ? 'Hide' : 'Show'} Details
          </button>
        )}
      </div>

      <div className="confidence-message">
        {config.message}
        {isPartialAnswer && (
          <span className="partial-answer-note">
            {' '}This is a partial answer based on available information.
          </span>
        )}
      </div>

      {isExpanded && (
        <div className="uncertainty-details">
          {missingInformation && missingInformation.length > 0 && (
            <div className="missing-info-section">
              <h4>📋 Missing Information</h4>
              <ul>
                {missingInformation.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {suggestions && suggestions.length > 0 && (
            <div className="suggestions-section">
              <h4>💡 Suggestions to Improve This Answer</h4>
              <ul>
                {suggestions.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

UncertaintyIndicator.propTypes = {
  confidenceLevel: PropTypes.oneOf(['high', 'medium', 'low', 'uncertain']),
  missingInformation: PropTypes.arrayOf(PropTypes.string),
  isPartialAnswer: PropTypes.bool,
  suggestions: PropTypes.arrayOf(PropTypes.string)
};

export default UncertaintyIndicator;
