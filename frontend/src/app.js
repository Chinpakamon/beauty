const API_ENDPOINTS = {
  login: '/user/login',
  registration: '/user/registration',
};

const authRoot = document.querySelector('#auth-app');

const state = {
  mode: 'login',
  isLoading: false,
  message: 'Выберите действие и отправьте форму.',
  messageType: '',
};

const fields = {
  login: [
    {
      name: 'email',
      label: 'Email',
      type: 'email',
      autocomplete: 'email',
      placeholder: 'client@example.com',
      required: true,
    },
    {
      name: 'password',
      label: 'Пароль',
      type: 'password',
      autocomplete: 'current-password',
      placeholder: 'Ваш пароль',
      required: true,
    },
  ],
  registration: [
    {
      name: 'first_name',
      label: 'Имя',
      type: 'text',
      autocomplete: 'given-name',
      placeholder: 'Анна',
      required: true,
      row: 'name',
    },
    {
      name: 'last_name',
      label: 'Фамилия',
      type: 'text',
      autocomplete: 'family-name',
      placeholder: 'Иванова',
      row: 'name',
    },
    {
      name: 'email',
      label: 'Email',
      type: 'email',
      autocomplete: 'email',
      placeholder: 'client@example.com',
      required: true,
    },
    {
      name: 'phone_number',
      label: 'Телефон',
      type: 'tel',
      autocomplete: 'tel',
      placeholder: '+79991234567',
      required: true,
    },
    {
      name: 'role',
      label: 'Роль',
      type: 'select',
      options: [
        ['USER', 'Клиент'],
        ['MASTER', 'Мастер'],
      ],
    },
    {
      name: 'password',
      label: 'Пароль',
      type: 'password',
      autocomplete: 'new-password',
      placeholder: 'Минимум 8 символов',
      required: true,
    },
  ],
};

const setState = (patch) => {
  Object.assign(state, patch);
  renderAuth();
};

const fieldTemplate = (field) => {
  const required = field.required ? 'required' : '';

  if (field.type === 'select') {
    const options = field.options
      .map(([value, label]) => `<option value="${value}">${label}</option>`)
      .join('');

    return `
      <label class="field">
        ${field.label}
        <select name="${field.name}">${options}</select>
      </label>
    `;
  }

  return `
    <label class="field">
      ${field.label}
      <input
        name="${field.name}"
        type="${field.type}"
        autocomplete="${field.autocomplete || 'off'}"
        placeholder="${field.placeholder || ''}"
        ${required}
      />
    </label>
  `;
};

const formTemplate = () => {
  const modeFields = fields[state.mode];
  const nameFields = modeFields.filter((field) => field.row === 'name');
  const restFields = modeFields.filter((field) => field.row !== 'name');
  const submitLabel = state.mode === 'login' ? 'Войти' : 'Зарегистрироваться';

  return `
    <form class="auth-form" data-mode="${state.mode}">
      ${nameFields.length ? `<div class="form-row">${nameFields.map(fieldTemplate).join('')}</div>` : ''}
      ${restFields.map(fieldTemplate).join('')}
      <button class="auth-submit" type="submit" ${state.isLoading ? 'disabled' : ''}>
        ${state.isLoading ? 'Отправляем...' : submitLabel}
      </button>
      <p class="message ${state.messageType}" role="status" aria-live="polite">
        ${state.message}
      </p>
    </form>
  `;
};

function renderAuth() {
  authRoot.innerHTML = `
    <div class="tabs" role="tablist" aria-label="Выбор формы авторизации">
      <button class="tab ${state.mode === 'login' ? 'is-active' : ''}" data-mode="login" type="button">Вход</button>
      <button class="tab ${state.mode === 'registration' ? 'is-active' : ''}" data-mode="registration" type="button">Регистрация</button>
    </div>
    ${formTemplate()}
  `;
}

const payloadFromForm = (form) => {
  const payload = Object.fromEntries(new FormData(form).entries());

  Object.keys(payload).forEach((key) => {
    if (payload[key] === '') {
      payload[key] = null;
    }
  });

  return payload;
};

const errorMessage = (body) => {
  if (Array.isArray(body.detail)) {
    return body.detail
      .map((item) => `${item.loc?.join('.') || 'field'}: ${item.msg}`)
      .join('; ');
  }

  return body.detail || 'Backend вернул ошибку. Проверьте данные формы.';
};

const submitAuth = async (form) => {
  const endpoint = API_ENDPOINTS[form.dataset.mode];

  setState({
    isLoading: true,
    message: 'Отправляем JSON на backend...',
    messageType: '',
  });

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payloadFromForm(form)),
    });
    const body = await response.json();

    if (!response.ok) {
      throw new Error(errorMessage(body));
    }

    localStorage.setItem('access_token', body.access_token);
    setState({
      message: 'Готово! Вы успешно зарегестрировались!',
      messageType: 'is-success',
    });
  } catch (error) {
    setState({ message: error.message, messageType: 'is-error' });
  } finally {
    setState({ isLoading: false });
  }
};

authRoot.addEventListener('click', (event) => {
  const tab = event.target.closest('[data-mode]');

  if (!tab || tab.matches('form')) {
    return;
  }

  setState({
    mode: tab.dataset.mode,
    message: 'Выберите действие и отправьте форму.',
    messageType: '',
  });
});

authRoot.addEventListener('submit', (event) => {
  event.preventDefault();
  submitAuth(event.target);
});

renderAuth();
