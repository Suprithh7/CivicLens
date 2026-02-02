/**
 * Custom hook for managing policies list
 * Handles fetching, filtering, and pagination of policies
 */

import { useState, useEffect, useCallback } from 'react';
import { listPolicies, deletePolicy } from '../services/api';
import { ITEMS_PER_PAGE } from '../constants';

export function usePolicies(initialFilters = {}) {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState({
    status: '',
    policyType: '',
    jurisdiction: '',
    ...initialFilters,
  });

  const fetchPolicies = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const offset = (currentPage - 1) * ITEMS_PER_PAGE;
      const response = await listPolicies({
        status: filters.status || null,
        policyType: filters.policyType || null,
        jurisdiction: filters.jurisdiction || null,
        limit: ITEMS_PER_PAGE,
        offset,
      });

      setPolicies(response.policies);
      setTotal(response.total);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [currentPage, filters]);

  useEffect(() => {
    fetchPolicies();
  }, [fetchPolicies]);

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({ ...prev, [filterName]: value }));
    setCurrentPage(1); // Reset to first page when filters change
  };

  const clearFilters = () => {
    setFilters({
      status: '',
      policyType: '',
      jurisdiction: '',
    });
    setCurrentPage(1);
  };

  const handleDelete = async (policyId) => {
    try {
      await deletePolicy(policyId);
      // Refresh the list
      await fetchPolicies();
      return true;
    } catch (err) {
      throw new Error(`Failed to delete policy: ${err.message}`);
    }
  };

  const hasFilters = filters.status || filters.policyType || filters.jurisdiction;

  return {
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
  };
}
