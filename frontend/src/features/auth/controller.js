import { apiRequest } from '../../shared/api.js';
import { setAccessToken } from '../../shared/storage.js';
import { AUTH_ENDPOINTS } from './config.js';

const payloadFromForm = (form) => {
  const payload = Object.fromEntries(new FormData(form).entries());

  Object.keys(payload).forEach((key) => {
    if (payload[key] === '') {
      payload[key] = null;
    }
  });

  return payload;
};

export const submitAuth = async (form) => {
  const mode = form.dataset.authForm;
  const body = await apiRequest(AUTH_ENDPOINTS[mode], {
    method: 'POST',
    body: JSON.stringify(payloadFromForm(form)),
  });

  setAccessToken(body.access_token);
  return mode;
};
