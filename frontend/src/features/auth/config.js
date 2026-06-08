export const AUTH_ENDPOINTS = {
  login: '/user/login',
  registration: '/user/registration',
};

export const AUTH_TABS = {
  login: 'Вход',
  registration: 'Регистрация',
};

export const AUTH_FIELDS = {
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
