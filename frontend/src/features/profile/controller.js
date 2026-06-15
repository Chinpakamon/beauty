import { apiRequest } from '../../shared/api.js';

const payloadFromForm = (form) => {
  const payload = Object.fromEntries(new FormData(form).entries());

  Object.keys(payload).forEach((key) => {
    if (payload[key] === '') {
      payload[key] = null;
    }
  });

  return payload;
};

export const loadProfile = () => apiRequest('/user/me');

export const updateProfile = (userId, form) => apiRequest(`/user/update/${userId}`, {
  method: 'POST',
  body: JSON.stringify(payloadFromForm(form)),
});
