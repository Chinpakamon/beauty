import { escapeHtml } from '../../shared/dom.js';
import { AUTH_FIELDS, AUTH_TABS } from './config.js';

const fieldTemplate = (field) => {
  if (field.type === 'select') {
    const options = field.options
      .map(([value, label]) => `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`)
      .join('');

    return `
      <label class="field">
        ${escapeHtml(field.label)}
        <select name="${escapeHtml(field.name)}">${options}</select>
      </label>
    `;
  }

  return `
    <label class="field">
      ${escapeHtml(field.label)}
      <input
        name="${escapeHtml(field.name)}"
        type="${escapeHtml(field.type)}"
        autocomplete="${escapeHtml(field.autocomplete || 'off')}"
        placeholder="${escapeHtml(field.placeholder || '')}"
        ${field.required ? 'required' : ''}
      />
    </label>
  `;
};

const authTabsTemplate = (mode) => `
  <div class="tabs" role="tablist" aria-label="Выбор формы авторизации">
    ${Object.entries(AUTH_TABS)
      .map(
        ([tabMode, label]) => `
          <button
            class="tab ${mode === tabMode ? 'is-active' : ''}"
            data-auth-mode="${tabMode}"
            type="button"
            role="tab"
            aria-selected="${mode === tabMode}"
          >${label}</button>
        `,
      )
      .join('')}
  </div>
`;

const authFormTemplate = (state) => {
  const modeFields = AUTH_FIELDS[state.authMode];
  const nameFields = modeFields.filter((field) => field.row === 'name');
  const restFields = modeFields.filter((field) => field.row !== 'name');
  const submitLabel = state.authMode === 'login' ? 'Продолжить' : 'Создать аккаунт';

  return `
    <form class="auth-form" data-auth-form="${state.authMode}">
      ${nameFields.length ? `<div class="form-row">${nameFields.map(fieldTemplate).join('')}</div>` : ''}
      ${restFields.map(fieldTemplate).join('')}
      <button class="auth-submit" type="submit" ${state.isLoading ? 'disabled' : ''}>
        ${state.isLoading ? 'Отправляем...' : submitLabel}
      </button>
      <p class="message ${state.messageType}" role="status" aria-live="polite">
        ${escapeHtml(state.message)}
      </p>
    </form>
  `;
};

export const renderAuthPage = (state) => `
  <section class="auth-landing" aria-labelledby="auth-title">
    <div class="auth-copy">
      <p class="eyebrow">Beauty workspace</p>
      <h1 id="auth-title">Добро пожаловать в «По красоте»</h1>
      <p>
        Выберите удобный сценарий: войдите в существующий аккаунт или создайте
        новый профиль клиента/мастера. После успешного выполнения приложение
        автоматически откроет личный кабинет.
      </p>
      <p class="auth-copy__note">
        Используйте форму справа: переключитесь между входом и регистрацией,
        заполните данные и продолжите работу в личном кабинете.
      </p>
    </div>
    <div id="auth-app" class="auth-panel">
      ${authTabsTemplate(state.authMode)}
      ${authFormTemplate(state)}
    </div>
  </section>
`;
