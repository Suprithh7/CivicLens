import React, { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import { askQuestionStreaming } from '../services/ragService';
import SourceCard from './SourceCard';
import EvaluationCard from './EvaluationCard';
import './RAGInterface.css';

/**
 * RAGInterface Component
 * Chat-like interface for asking questions about policy documents
 */
const RAGInterface = ({ policyId = null }) => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!query.trim()) return;

    const userMessage = {
      type: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setIsLoading(true);
    setError(null);

    // Create assistant message placeholder
    const assistantMessage = {
      type: 'assistant',
      content: '',
      sources: [],
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      await askQuestionStreaming({
        query: userMessage.content,
        policyId,
        topK: 5,
        onChunk: (chunk) => {
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];

            if (chunk.type === 'sources') {
              lastMessage.sources = chunk.sources || [];
            } else if (chunk.type === 'answer') {
              if (chunk.done) {
                lastMessage.isStreaming = false;
              } else {
                lastMessage.content += chunk.content || '';
              }
            } else if (chunk.type === 'evaluation') {
              lastMessage.evaluation = chunk.evaluation;
            }

            return newMessages;
          });
        },
        onError: (err) => {
          setError(err.message || 'Failed to get answer');
          setIsLoading(false);
        },
      });

      setIsLoading(false);
    } catch (err) {
      setError(err.message || 'Failed to get answer');
      setIsLoading(false);

      // Remove the failed assistant message
      setMessages(prev => prev.slice(0, -1));
    }
  };

  const handleClear = () => {
    setMessages([]);
    setError(null);
  };

  const handleCopyAnswer = (content) => {
    navigator.clipboard.writeText(content);
  };

  return (
    <div className="rag-interface">
      <div className="rag-header">
        <h2>Ask Questions About Policies</h2>
        <p className="rag-subtitle">
          {policyId
            ? 'Ask questions about this specific policy document'
            : 'Ask questions across all policy documents'}
        </p>
      </div>

      <div className="rag-messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">💬</div>
            <h3>Start a Conversation</h3>
            <p>Ask any question about the policy documents and get AI-powered answers with source citations.</p>
            <div className="example-questions">
              <p className="example-title">Example questions:</p>
              <ul>
                <li>"What are the eligibility criteria?"</li>
                <li>"How do I apply for this program?"</li>
                <li>"What documents are required?"</li>
              </ul>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index} className={`message message-${message.type}`}>
            {message.type === 'user' ? (
              <div className="message-content user-message">
                <div className="message-avatar">👤</div>
                <div className="message-text">{message.content}</div>
              </div>
            ) : (
              <div className="message-content assistant-message">
                <div className="message-avatar">🤖</div>
                <div className="message-body">
                  {message.content && (
                    <div className="message-text">
                      {message.content}
                      {message.isStreaming && <span className="cursor">▊</span>}
                    </div>
                  )}

                  {!message.isStreaming && message.content && (
                    <button
                      className="copy-button"
                      onClick={() => handleCopyAnswer(message.content)}
                      title="Copy answer"
                    >
                      📋 Copy
                    </button>
                  )}

                  {message.sources && message.sources.length > 0 && (
                    <div className="sources-section">
                      <h4 className="sources-title">
                        📚 Sources ({message.sources.length})
                      </h4>
                      <div className="sources-list">
                        {message.sources.map((source, idx) => (
                          <SourceCard
                            key={source.chunk_id}
                            source={source}
                            index={idx}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {message.evaluation && (
                    <EvaluationCard evaluation={message.evaluation} />
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="rag-input-container">
        {messages.length > 0 && (
          <button
            className="clear-button"
            onClick={handleClear}
            disabled={isLoading}
          >
            🗑️ Clear Conversation
          </button>
        )}

        <form onSubmit={handleSubmit} className="rag-input-form">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about the policies..."
            className="rag-input"
            disabled={isLoading}
          />
          <button
            type="submit"
            className="rag-submit"
            disabled={isLoading || !query.trim()}
          >
            {isLoading ? '⏳' : '🚀'} {isLoading ? 'Thinking...' : 'Ask'}
          </button>
        </form>
      </div>
    </div>
  );
};

RAGInterface.propTypes = {
  policyId: PropTypes.string,
};

export default RAGInterface;
