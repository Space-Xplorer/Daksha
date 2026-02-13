/**
 * Workflow Service
 */
import api from './api';

export const workflowService = {
  /**
   * Submit application for workflow processing
   */
  async submit(appId) {
    const response = await api.post(`/api/workflow/submit/${appId}`);
    return response.data;
  },

  /**
   * Get workflow execution status
   */
  async getStatus(appId) {
    const response = await api.get(`/api/workflow/status/${appId}`);
    return response.data;
  },

  /**
   * Get workflow results
   */
  async getResults(appId) {
    const response = await api.get(`/api/workflow/results/${appId}`);
    return response.data;
  },

  /**
   * Get HITL checkpoint data
   */
  async getHITL(appId) {
    const response = await api.get(`/api/workflow/hitl/${appId}`);
    return response.data;
  },

  /**
   * Approve HITL with optional corrections
   */
  async approveHITL(appId, corrections = {}) {
    const response = await api.post(`/api/workflow/hitl/${appId}/approve`, {
      corrections,
    });
    return response.data;
  },

  /**
   * Poll workflow status until completion
   * @param {string} appId - Application ID
   * @param {function} onProgress - Callback for progress updates
   * @param {number} interval - Polling interval in ms (default: 2000)
   * @returns {Promise} - Resolves with final results
   */
  async pollStatus(appId, onProgress, interval = 2000) {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const status = await this.getStatus(appId);
          
          // Call progress callback
          if (onProgress) {
            onProgress(status);
          }

          // Check if completed
          if (status.status === 'completed') {
            const results = await this.getResults(appId);
            resolve(results);
            return;
          }

          // Check if failed
          if (status.status === 'failed') {
            reject(new Error(status.error || 'Workflow failed'));
            return;
          }

          // Check if waiting for HITL
          if (status.status === 'hitl_pending') {
            resolve({ status: 'hitl_pending', data: status });
            return;
          }

          // Continue polling
          setTimeout(poll, interval);
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  },
};
