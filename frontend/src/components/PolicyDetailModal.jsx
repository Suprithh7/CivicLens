import React, { useState, useEffect } from 'react';
import { updatePolicy, getPolicyVersions, restorePolicyVersion } from '../services/api';
import { POLICY_TYPE_OPTIONS } from '../constants';
import LoadingSpinner from './common/LoadingSpinner';

const PolicyDetailModal = ({ policy, isOpen, onClose, onPolicyUpdated }) => {
  const [activeTab, setActiveTab] = useState('details'); // 'details', 'edit', 'history'
  const [versions, setVersions] = useState([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  const [error, setError] = useState(null);

  // Edit form state
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    policy_type: '',
    jurisdiction: '',
    change_reason: ''
  });
  const [saving, setSaving] = useState(false);
  const [restoring, setRestoring] = useState(false);

  useEffect(() => {
    if (policy && isOpen) {
      setEditForm({
        title: policy.title || '',
        description: policy.description || '',
        policy_type: policy.policy_type || '',
        jurisdiction: policy.jurisdiction || '',
        change_reason: ''
      });
      setActiveTab('details');
      setError(null);
    }
  }, [policy, isOpen]);

  useEffect(() => {
    if (isOpen && activeTab === 'history' && policy) {
      loadVersions();
    }
  }, [isOpen, activeTab, policy]);

  const loadVersions = async () => {
    setLoadingVersions(true);
    setError(null);
    try {
      const data = await getPolicyVersions(policy.policy_id);
      setVersions(data.versions || []);
    } catch (err) {
      setError(err.message || 'Failed to load version history');
    } finally {
      setLoadingVersions(false);
    }
  };

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updateData = {
        title: editForm.title || null,
        description: editForm.description || null,
        policy_type: editForm.policy_type || null,
        jurisdiction: editForm.jurisdiction || null,
        change_reason: editForm.change_reason || 'Updated via UI',
        changed_by: 'current_user' // In a real app, get from auth
      };

      // Clean undefined/null values that are empty strings
      Object.keys(updateData).forEach(key => {
        if (updateData[key] === '') updateData[key] = null;
      });

      const updatedPolicy = await updatePolicy(policy.policy_id, updateData);
      onPolicyUpdated(updatedPolicy);
      setActiveTab('details');
      // Reset reason
      setEditForm(prev => ({ ...prev, change_reason: '' }));
    } catch (err) {
      setError(err.message || 'Failed to update policy');
    } finally {
      setSaving(false);
    }
  };

  const handleRestore = async (versionNumber) => {
    if (!window.confirm(`Are you sure you want to restore to version ${versionNumber}? Current changes will be snapshotted but overwritten.`)) {
      return;
    }

    setRestoring(true);
    setError(null);
    try {
      const restoredPolicy = await restorePolicyVersion(policy.policy_id, versionNumber);
      onPolicyUpdated(restoredPolicy);
      await loadVersions(); // Reload history
      setActiveTab('details');
    } catch (err) {
      setError(err.message || 'Failed to restore version');
    } finally {
      setRestoring(false);
    }
  };

  if (!isOpen || !policy) return null;

  // Format date helper
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const formatPolicyType = (type) => {
    if (!type) return 'N/A';
    const option = POLICY_TYPE_OPTIONS.find(o => o.value === type);
    return option ? option.label : type;
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75" onClick={onClose}></div>
        </div>

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
          {/* Header */}
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h3 className="text-xl leading-6 font-semibold text-gray-900" id="modal-title">
                {policy.title || policy.filename}
                <span className="ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  v{policy.version}
                </span>
              </h3>
              <button
                type="button"
                className="bg-white rounded-md text-gray-400 hover:text-gray-500 focus:outline-none"
                onClick={onClose}
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <p className="text-sm text-gray-500 mt-1 font-mono">{policy.policy_id}</p>

            {/* Tabs */}
            <div className="mt-6 border-b border-gray-200">
              <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                <button
                  onClick={() => setActiveTab('details')}
                  className={`${activeTab === 'details' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                >
                  Details
                </button>
                <button
                  onClick={() => setActiveTab('edit')}
                  className={`${activeTab === 'edit' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                >
                  Edit Metadata
                </button>
                <button
                  onClick={() => setActiveTab('history')}
                  className={`${activeTab === 'history' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                >
                  Version History
                </button>
              </nav>
            </div>

            {error && (
              <div className="mt-4 bg-red-50 border-l-4 border-red-400 p-4">
                <div className="flex">
                  <div className="ml-3">
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Content */}
          <div className="bg-gray-50 px-4 py-5 sm:p-6" style={{ minHeight: '300px', maxHeight: '60vh', overflowY: 'auto' }}>

            {/* Details Tab */}
            {activeTab === 'details' && (
              <div className="space-y-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-500">Description</h4>
                  <p className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                    {policy.description || 'No description provided.'}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Policy Type</h4>
                    <p className="mt-1 text-sm text-gray-900">{formatPolicyType(policy.policy_type)}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Jurisdiction</h4>
                    <p className="mt-1 text-sm text-gray-900">{policy.jurisdiction || 'N/A'}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Status</h4>
                    <p className="mt-1 text-sm text-gray-900 capitalize">{policy.status}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Language</h4>
                    <p className="mt-1 text-sm text-gray-900 uppercase">{policy.language || 'EN'}</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">File Info</h4>
                    <p className="mt-1 text-sm text-gray-900">{policy.filename} ({(policy.file_size / 1024).toFixed(1)} KB)</p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Last Updated</h4>
                    <p className="mt-1 text-sm text-gray-900">{formatDate(policy.updated_at)}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Edit Tab */}
            {activeTab === 'edit' && (
              <form id="edit-policy-form" onSubmit={handleSaveEdit} className="space-y-4">
                <div>
                  <label htmlFor="title" className="block text-sm font-medium text-gray-700">Title</label>
                  <input
                    type="text"
                    name="title"
                    id="title"
                    value={editForm.title}
                    onChange={handleEditChange}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
                  />
                </div>

                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">Description</label>
                  <textarea
                    name="description"
                    id="description"
                    rows={3}
                    value={editForm.description}
                    onChange={handleEditChange}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="policy_type" className="block text-sm font-medium text-gray-700">Policy Type</label>
                    <select
                      name="policy_type"
                      id="policy_type"
                      value={editForm.policy_type}
                      onChange={handleEditChange}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border bg-white"
                    >
                      <option value="">Select Type...</option>
                      {POLICY_TYPE_OPTIONS.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="jurisdiction" className="block text-sm font-medium text-gray-700">Jurisdiction</label>
                    <input
                      type="text"
                      name="jurisdiction"
                      id="jurisdiction"
                      value={editForm.jurisdiction}
                      onChange={handleEditChange}
                      placeholder="e.g., California, USA"
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
                    />
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-200">
                  <label htmlFor="change_reason" className="block text-sm font-medium text-gray-700">
                    Reason for Change <span className="text-gray-400 font-normal">(stored in version history)</span>
                  </label>
                  <input
                    type="text"
                    name="change_reason"
                    id="change_reason"
                    required
                    value={editForm.change_reason}
                    onChange={handleEditChange}
                    placeholder="Briefly describe what you changed and why"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
                  />
                </div>
              </form>
            )}

            {/* History Tab */}
            {activeTab === 'history' && (
              <div className="space-y-4">
                {loadingVersions ? (
                  <div className="flex justify-center py-8">
                    <LoadingSpinner />
                  </div>
                ) : versions.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p>No previous versions found for this policy.</p>
                  </div>
                ) : (
                  <div className="flow-root">
                    <ul className="-mb-8">
                      {/* Current version representation at the top */}
                      <li>
                        <div className="relative pb-8">
                          <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true"></span>
                          <div className="relative flex space-x-3">
                            <div>
                              <span className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center ring-8 ring-white">
                                <span className="text-white text-xs font-bold font-mono">v{policy.version}</span>
                              </span>
                            </div>
                            <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                              <div>
                                <p className="text-sm text-gray-900 font-medium">Current Version</p>
                                <p className="mt-1 text-sm text-gray-500">Active state of the policy</p>
                              </div>
                              <div className="text-right text-sm whitespace-nowrap text-gray-500">
                                Last updated: {formatDate(policy.updated_at)}
                              </div>
                            </div>
                          </div>
                        </div>
                      </li>

                      {/* Historical versions */}
                      {versions.map((version, versionIdx) => (
                        <li key={version.id}>
                          <div className="relative pb-8">
                            {versionIdx !== versions.length - 1 ? (
                              <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true"></span>
                            ) : null}
                            <div className="relative flex space-x-3">
                              <div>
                                <span className="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center ring-8 ring-white">
                                  <span className="text-white text-xs font-bold font-mono">v{version.version_number}</span>
                                </span>
                              </div>
                              <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                                <div>
                                  <p className="text-sm text-gray-900 font-medium">Snapshot v{version.version_number}</p>
                                  <p className="mt-1 text-sm text-gray-500 italic">"{version.change_reason || 'No reason provided'}"</p>
                                  <p className="mt-0.5 text-xs text-gray-400">By {version.changed_by || 'Unknown user'}</p>
                                </div>
                                <div className="text-right text-sm whitespace-nowrap flex flex-col items-end gap-2">
                                  <span className="text-gray-500">{formatDate(version.created_at)}</span>
                                  <button
                                    onClick={() => handleRestore(version.version_number)}
                                    disabled={restoring}
                                    className="text-xs bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 px-2 py-1 rounded shadow-sm disabled:opacity-50"
                                  >
                                    Restore to v{version.version_number}
                                  </button>
                                </div>
                              </div>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer actions */}
          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse border-t border-gray-200">
            {activeTab === 'edit' && (
              <button
                type="submit"
                form="edit-policy-form"
                disabled={saving || !editForm.change_reason}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            )}
            <button
              type="button"
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              onClick={onClose}
            >
              {activeTab === 'edit' ? 'Cancel' : 'Close'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PolicyDetailModal;
