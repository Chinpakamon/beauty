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

const compactObject = (object) => Object.fromEntries(
  Object.entries(object).filter(([, value]) => value !== null && value !== undefined && value !== ''),
);

const listPayloadFromForm = (form, baseFilters = {}) => {
  const values = Object.fromEntries(new FormData(form).entries());
  const limit = Number(values.limit || 10);
  const offset = Number(values.offset || 0);
  const { order_by: orderBy = null } = values;
  delete values.limit;
  delete values.offset;
  delete values.order_by;

  return {
    filters: compactObject({ ...baseFilters, ...values }),
    order_by: orderBy || null,
    limit,
    offset,
  };
};

export const loadProfile = () => apiRequest('/user/me');

export const updateProfile = (userId, form) => apiRequest(`/user/update/${userId}`, {
  method: 'POST',
  body: JSON.stringify(payloadFromForm(form)),
});

export const listSpecialists = (form = null) => apiRequest('/user/list', {
  method: 'POST',
  body: JSON.stringify(form ? listPayloadFromForm(form, { role: 'MASTER' }) : {
    filters: { role: 'MASTER' },
    order_by: 'FIRST_NAME_ASC',
    limit: 20,
    offset: 0,
  }),
});

export const listServices = (form = null) => apiRequest('/service/list', {
  method: 'POST',
  body: JSON.stringify(form ? listPayloadFromForm(form) : {
    filters: {},
    order_by: 'CREATED_AT_DESC',
    limit: 20,
    offset: 0,
  }),
});
