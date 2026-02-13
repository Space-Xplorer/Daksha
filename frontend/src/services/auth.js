/**
 * Authentication Service
 */
import api from './api';

export const authService = {
  /**
   * Register a new user
   */
  async register(email, password, name) {
    const response = await api.post('/api/auth/register', {
      email,
      password,
      name,
    });
    return response.data;
  },

  /**
   * Login user
   */
  async login(email, password) {
    const response = await api.post('/api/auth/login', {
      email,
      password,
    });

    const { access_token, refresh_token, user } = response.data;

    // Store tokens and user info
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('user', JSON.stringify(user));

    return response.data;
  },

  /**
   * Logout user
   */
  async logout() {
    try {
      await api.post('/api/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage regardless of API call result
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },

  /**
   * Get current user info
   */
  async getCurrentUser() {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  /**
   * Refresh access token
   */
  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await api.post('/api/auth/refresh', {
      refresh_token: refreshToken,
    });

    const { access_token } = response.data;
    localStorage.setItem('access_token', access_token);

    return response.data;
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated() {
    return !!localStorage.getItem('access_token');
  },

  /**
   * Get stored user info
   */
  getUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
};
