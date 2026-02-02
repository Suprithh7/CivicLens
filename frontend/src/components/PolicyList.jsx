import React from 'react';
import PolicyCard from './PolicyCard';
import LoadingSpinner from './common/LoadingSpinner';
import ErrorMessage from './common/ErrorMessage';
import { usePolicies } from '../hooks/usePolicies';
import { usePagination } from '../hooks/usePagination';
import { ITEMS_PER_PAGE, POLICY_STATUS_OPTIONS, POLICY_TYPE_OPTIONS } from '../constants';

/**
 * PolicyList Component
 * Displays a paginated, filterable list of uploaded policies
 */
const PolicyList = () => {
  const {
    policies,
    loading,
    error,
    total,
    currentPage,
    filters,
    hasFilters,
    setCurrentPage,
    handleFilterChange,
    clearFilters,
    fetchPolicies,
    handleDelete,
  } = usePolicies();

  const { totalPages, getPageNumbers } = usePagination(total, ITEMS_PER_PAGE);

  const handleView = (policy) => {
    // For now, just log - we'll implement a modal or detail page later
    console.log('View policy:', policy);
    alert(`Viewing policy: ${policy.title || policy.filename}\n\nPolicy ID: ${policy.policy_id}\nStatus: ${policy.status}`);
  };

  const onDelete = async (policy) => {
    if (!confirm(`Are you sure you want to delete "${policy.title || policy.filename}"?`)) {
      return;
    }

    try {
      await handleDelete(policy.policy_id);
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-800">Policy Documents</h2>
          <p className="text-gray-600 mt-1">
            {total} {total === 1 ? 'policy' : 'policies'} uploaded
          </p>
        </div>
        <button
          onClick={fetchPolicies}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800">Filters</h3>
          {hasFilters && (
            <button
              onClick={clearFilters}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Clear All
            </button>
          )}
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {POLICY_STATUS_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          {/* Policy Type Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Policy Type
            </label>
            <select
              value={filters.policyType}
              onChange={(e) => handleFilterChange('policyType', e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {POLICY_TYPE_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          {/* Jurisdiction Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Jurisdiction
            </label>
            <input
              type="text"
              value={filters.jurisdiction}
              onChange={(e) => handleFilterChange('jurisdiction', e.target.value)}
              placeholder="e.g., Karnataka, India"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && <LoadingSpinner />}

      {/* Error State */}
      {error && (
        <ErrorMessage
          title="Error loading policies"
          message={error}
          onRetry={fetchPolicies}
        />
      )}

      {/* Empty State */}
      {!loading && !error && policies.length === 0 && (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">No policies found</h3>
          <p className="text-gray-600">
            {hasFilters
              ? 'Try adjusting your filters or upload a new policy document.'
              : 'Upload your first policy document to get started.'}
          </p>
        </div>
      )}

      {/* Policy Grid */}
      {!loading && !error && policies.length > 0 && (
        <>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {policies.map((policy) => (
              <PolicyCard
                key={policy.id}
                policy={policy}
                onView={handleView}
                onDelete={onDelete}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-6">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>

              <div className="flex gap-1">
                {getPageNumbers(currentPage).map((page, index) => {
                  if (page === '...') {
                    return <span key={`ellipsis-${index}`} className="px-2 py-2">...</span>;
                  }
                  return (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`px-4 py-2 rounded-lg transition-colors ${currentPage === page
                        ? 'bg-blue-600 text-white'
                        : 'border border-gray-300 hover:bg-gray-50'
                        }`}
                    >
                      {page}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default PolicyList;
