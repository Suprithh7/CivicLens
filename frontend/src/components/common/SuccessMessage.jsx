import React from 'react';

/**
 * Reusable success message component
 */
function SuccessMessage({ title = 'Success', message, details, className = '' }) {
  return (
    <div className={`bg-green-50 border border-green-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start space-x-2">
        <svg className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div className="flex-1">
          <p className="text-sm font-medium text-green-800">{title}</p>
          {message && <p className="text-xs text-green-700 mt-1">{message}</p>}
          {details && (
            <div className="mt-2 text-xs text-green-700 space-y-1">
              {details}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SuccessMessage;
