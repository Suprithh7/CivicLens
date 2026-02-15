import React from 'react';
import PropTypes from 'prop-types';
import './ScenarioExplanation.css';

/**
 * ScenarioExplanation Component
 * Displays scenario-based policy explanations with structured formatting
 */
const ScenarioExplanation = ({ explanation, scenarioType, policyTitle }) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(explanation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Parse the explanation into sections
  const parseExplanation = (text) => {
    const sections = {
      applies: '',
      benefits: '',
      requirements: '',
      nextSteps: '',
      dates: '',
      documents: ''
    };

    // Try to extract sections based on common headers
    const applyMatch = text.match(/\*\*Does This Apply to You\?\*\*[:\s]*([\s\S]*?)(?=\*\*|$)/i);
    const benefitsMatch = text.match(/\*\*What You Get\*\*[:\s]*([\s\S]*?)(?=\*\*|$)/i);
    const requirementsMatch = text.match(/\*\*What You Need\*\*[:\s]*([\s\S]*?)(?=\*\*|$)/i);
    const stepsMatch = text.match(/\*\*Next Steps\*\*[:\s]*([\s\S]*?)(?=\*\*|$)/i);
    const datesMatch = text.match(/\*\*Important Dates\*\*[:\s]*([\s\S]*?)(?=\*\*|$)/i);
    const docsMatch = text.match(/\*\*Required Documents\*\*[:\s]*([\s\S]*?)(?=\*\*|$)/i);

    if (applyMatch) sections.applies = applyMatch[1].trim();
    if (benefitsMatch) sections.benefits = benefitsMatch[1].trim();
    if (requirementsMatch) sections.requirements = requirementsMatch[1].trim();
    if (stepsMatch) sections.nextSteps = stepsMatch[1].trim();
    if (datesMatch) sections.dates = datesMatch[1].trim();
    if (docsMatch) sections.documents = docsMatch[1].trim();

    return sections;
  };

  const sections = parseExplanation(explanation);

  return (
    <div className="scenario-explanation">
      <div className="explanation-header">
        <div className="header-content">
          <h3>Scenario-Based Guidance</h3>
          {policyTitle && <p className="policy-title">{policyTitle}</p>}
        </div>
        <button
          className={`copy-btn ${copied ? 'copied' : ''}`}
          onClick={handleCopy}
          title="Copy explanation"
        >
          {copied ? '✓ Copied!' : '📋 Copy'}
        </button>
      </div>

      <div className="explanation-content">
        {sections.applies && (
          <div className="explanation-section applies-section">
            <div className="section-header">
              <span className="section-icon">✓</span>
              <h4>Does This Apply to You?</h4>
            </div>
            <div className="section-content">
              {sections.applies}
            </div>
          </div>
        )}

        {sections.benefits && (
          <div className="explanation-section benefits-section">
            <div className="section-header">
              <span className="section-icon">🎁</span>
              <h4>What You Get</h4>
            </div>
            <div className="section-content">
              {sections.benefits}
            </div>
          </div>
        )}

        {sections.requirements && (
          <div className="explanation-section requirements-section">
            <div className="section-header">
              <span className="section-icon">📋</span>
              <h4>What You Need</h4>
            </div>
            <div className="section-content">
              {sections.requirements}
            </div>
          </div>
        )}

        {sections.nextSteps && (
          <div className="explanation-section steps-section">
            <div className="section-header">
              <span className="section-icon">🚀</span>
              <h4>Next Steps</h4>
            </div>
            <div className="section-content">
              {sections.nextSteps}
            </div>
          </div>
        )}

        {sections.dates && (
          <div className="explanation-section dates-section">
            <div className="section-header">
              <span className="section-icon">📅</span>
              <h4>Important Dates</h4>
            </div>
            <div className="section-content">
              {sections.dates}
            </div>
          </div>
        )}

        {sections.documents && (
          <div className="explanation-section documents-section">
            <div className="section-header">
              <span className="section-icon">📄</span>
              <h4>Required Documents</h4>
            </div>
            <div className="section-content">
              {sections.documents}
            </div>
          </div>
        )}

        {/* Fallback: if no sections parsed, show full text */}
        {!sections.applies && !sections.benefits && !sections.requirements &&
          !sections.nextSteps && !sections.dates && !sections.documents && (
            <div className="explanation-section">
              <div className="section-content">
                {explanation}
              </div>
            </div>
          )}
      </div>
    </div>
  );
};

ScenarioExplanation.propTypes = {
  explanation: PropTypes.string.isRequired,
  scenarioType: PropTypes.string,
  policyTitle: PropTypes.string
};

export default ScenarioExplanation;
