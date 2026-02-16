import React from 'react';
import PropTypes from 'prop-types';
import './EvaluationCard.css';

/**
 * EvaluationCard Component
 * Displays evaluation metrics for AI-generated responses
 */
const EvaluationCard = ({ evaluation }) => {
  if (!evaluation) return null;

  const {
    relevance_score,
    coherence_score,
    completeness_score,
    source_grounding_score,
    hallucination_risk,
    safety_score,
    quality_flags = [],
    overall_confidence
  } = evaluation;

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'score-high';
    if (score >= 0.5) return 'score-medium';
    return 'score-low';
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'low': return 'risk-low';
      case 'medium': return 'risk-medium';
      case 'high': return 'risk-high';
      default: return '';
    }
  };

  return (
    <div className="evaluation-card">
      <div className="evaluation-header">
        <div className="evaluation-title">
          <span>🎯 Assessment</span>
          <span className={`confidence-badge ${getScoreColor(overall_confidence)}`}>
            {Math.round(overall_confidence * 100)}% Confidence
          </span>
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-item">
          <span className="metric-label">Relevance</span>
          <div className="metric-bar-container">
            <div
              className={`metric-bar ${getScoreColor(relevance_score)}`}
              style={{ width: `${relevance_score * 100}%` }}
            />
          </div>
        </div>

        <div className="metric-item">
          <span className="metric-label">Coherence</span>
          <div className="metric-bar-container">
            <div
              className={`metric-bar ${getScoreColor(coherence_score)}`}
              style={{ width: `${coherence_score * 100}%` }}
            />
          </div>
        </div>

        <div className="metric-item">
          <span className="metric-label">Completeness</span>
          <div className="metric-bar-container">
            <div
              className={`metric-bar ${getScoreColor(completeness_score)}`}
              style={{ width: `${completeness_score * 100}%` }}
            />
          </div>
        </div>

        <div className="metric-item">
          <span className="metric-label">Source Grounding</span>
          <div className="metric-bar-container">
            <div
              className={`metric-bar ${getScoreColor(source_grounding_score)}`}
              style={{ width: `${source_grounding_score * 100}%` }}
            />
          </div>
        </div>
      </div>

      <div className="risk-section">
        <div className="risk-item">
          <span className="risk-label">Hallucination Risk:</span>
          <span className={`risk-value ${getRiskColor(hallucination_risk)}`}>
            {hallucination_risk.toUpperCase()}
          </span>
        </div>

        {safety_score < 1.0 && (
          <div className="risk-item">
            <span className="risk-label">Safety Score:</span>
            <span className={`risk-value ${getScoreColor(safety_score)}`}>
              {Math.round(safety_score * 100)}%
            </span>
          </div>
        )}
      </div>

      {quality_flags.length > 0 && (
        <div className="flags-section">
          {quality_flags.map((flag, index) => (
            <span key={index} className="quality-flag">
              ⚠️ {flag.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

EvaluationCard.propTypes = {
  evaluation: PropTypes.shape({
    relevance_score: PropTypes.number,
    coherence_score: PropTypes.number,
    completeness_score: PropTypes.number,
    source_grounding_score: PropTypes.number,
    hallucination_risk: PropTypes.string,
    safety_score: PropTypes.number,
    quality_flags: PropTypes.arrayOf(PropTypes.string),
    overall_confidence: PropTypes.number
  })
};

export default EvaluationCard;
