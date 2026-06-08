import { getAccessToken } from './storage.js';

export const apiRequest = async (url, options = {}) => {
  const token = getAccessToken();
  const headers = {
    ...(options.body ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });
  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json') ? await response.json() : null;

  if (!response.ok) {
    throw new Error(formatApiError(body));
  }

  return body;
};

export const formatApiError = (body) => {
  if (Array.isArray(body?.detail)) {
    return body.detail
      .map((item) => `${item.loc?.join('.') || 'field'}: ${item.msg}`)
      .join('; ');
  }

  return body?.detail || 'Backend вернул ошибку. Проверьте данные формы.';
};
