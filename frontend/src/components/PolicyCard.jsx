import React from 'react';

/**
 * PolicyCard Component
 * Displays a single policy in a card format with status badges and metadata
 */
const PolicyCard = ({ policy, onView, onDelete }) => {
  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Get status badge color
  const getStatusColor = (status) => {
    const colors = {
      uploaded: 'bg-blue-100 text-blue-800',
      processing: 'bg-yellow-100 text-yellow-800',
      analyzed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      archived: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  // Get policy type badge color
  const getPolicyTypeColor = (type) => {
    const colors = {
      healthcare: 'bg-pink-100 text-pink-800',
      education: 'bg-indigo-100 text-indigo-800',
      agriculture: 'bg-green-100 text-green-800',
      employment: 'bg-purple-100 text-purple-800',
      housing: 'bg-orange-100 text-orange-800',
      social_welfare: 'bg-teal-100 text-teal-800',
      infrastructure: 'bg-gray-100 text-gray-800',
      environment: 'bg-emerald-100 text-emerald-800',
      finance: 'bg-blue-100 text-blue-800',
      other: 'bg-slate-100 text-slate-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  // Format policy type for display
  const formatPolicyType = (type) => {
    if (!type) return null;
    return type.split('_').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6 border border-gray-200">
      {/* Header with title and status */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-800 mb-1 line-clamp-2">
            {policy.title || policy.filename}
          </h3>
          <p className="text-sm text-gray-500 font-mono">{policy.policy_id}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(policy.status)}`}>
          {policy.status}
        </span>
      </div>

      {/* Description */}
      {policy.description && (
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
          {policy.description}
        </p>
      )}

      {/* Metadata */}
      <div className="space-y-2 mb-4">
        {/* Policy Type */}
        {policy.policy_type && (
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            </svg>
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${getPolicyTypeColor(policy.policy_type)}`}>
              {formatPolicyType(policy.policy_type)}
            </span>
          </div>
        )}

        {/* Jurisdiction */}
        {policy.jurisdiction && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span>{policy.jurisdiction}</span>
          </div>
        )}

        {/* File info */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>{policy.filename}</span>
          <span className="text-gray-400">•</span>
          <span>{formatFileSize(policy.file_size)}</span>
        </div>

        {/* Upload date */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span>Uploaded {formatDate(policy.created_at)}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-4 border-t border-gray-200">
        <button
          onClick={() => onView(policy)}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg transition-colors text-sm"
        >
          View Details
        </button>
        <button
          onClick={() => onDelete(policy)}
          className="bg-red-50 hover:bg-red-100 text-red-600 font-medium px-4 py-2 rounded-lg transition-colors text-sm"
        >
          Delete
        </button>
      </div>
    </div>
  );
};

export default PolicyCard;

