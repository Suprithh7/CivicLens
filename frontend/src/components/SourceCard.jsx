import React from 'react';
import PropTypes from 'prop-types';
import './SourceCard.css';

/**
 * SourceCard Component
 * Displays a source chunk with metadata from RAG results
 */
const SourceCard = ({ source, index, onExpand }) => {
  const [isExpanded, setIsExpanded] = React.useState(false);

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
    if (onExpand) onExpand(source, !isExpanded);
  };

  const truncateText = (text, maxLength = 150) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const getSimilarityColor = (score) => {
    if (score >= 0.8) return '#10b981'; // green
    if (score >= 0.6) return '#f59e0b'; // amber
    return '#6b7280'; // gray
  };

  return (
    <div className="source-card">
      <div className="source-header">
        <div className="source-title">
          <span className="source-number">Source {index + 1}</span>
          <span className="policy-title">{source.policy_title || 'Unknown Policy'}</span>
        </div>
        <div
          className="similarity-badge"
          style={{ backgroundColor: getSimilarityColor(source.similarity_score) }}
        >
          {(source.similarity_score * 100).toFixed(0)}% match
        </div>
      </div>

      <div className="source-content">
        <p className="chunk-text">
          {isExpanded ? source.chunk_text : truncateText(source.chunk_text)}
        </p>
      </div>

      <div className="source-footer">
        <div className="source-metadata">
          <span className="metadata-item">Chunk {source.chunk_index + 1}</span>
          <span className="metadata-item">
            Position: {source.start_char}-{source.end_char}
          </span>
        </div>
        <button
          className="expand-button"
          onClick={handleToggle}
        >
          {isExpanded ? 'Show Less' : 'Show More'}
        </button>
      </div>
    </div>
  );
};

SourceCard.propTypes = {
  source: PropTypes.shape({
    chunk_id: PropTypes.number.isRequired,
    chunk_text: PropTypes.string.isRequired,
    chunk_index: PropTypes.number.isRequired,
    policy_id: PropTypes.string.isRequired,
    policy_title: PropTypes.string,
    similarity_score: PropTypes.number.isRequired,
    start_char: PropTypes.number.isRequired,
    end_char: PropTypes.number.isRequired,
  }).isRequired,
  index: PropTypes.number.isRequired,
  onExpand: PropTypes.func,
};

export default SourceCard;
