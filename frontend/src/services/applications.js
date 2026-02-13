/**
 * Applications Service
 */
import api from './api';

export const applicationsService = {
  /**
   * Create a new application
   */
  async create(data) {
    const response = await api.post('/api/applications/', data);
    return response.data.application || response.data;
  },

  /**
   * Get all applications for current user
   */
  async getAll() {
    const response = await api.get('/api/applications/');
    return response.data.applications || response.data;
  },

  /**
   * Get specific application by ID
   */
  async getById(appId) {
    const response = await api.get(`/api/applications/${appId}`);
    return response.data.application || response.data;
  },

  /**
   * Update an application
   */
  async update(appId, data) {
    const response = await api.put(`/api/applications/${appId}`, data);
    return response.data.application || response.data;
  },

  /**
   * Delete an application
   */
  async delete(appId) {
    const response = await api.delete(`/api/applications/${appId}`);
    return response.data;
  },
};
