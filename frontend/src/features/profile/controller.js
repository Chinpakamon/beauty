import { apiRequest } from '../../shared/api.js';

export const loadProfile = () => apiRequest('/user/me');
