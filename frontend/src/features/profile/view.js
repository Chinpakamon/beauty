import { escapeHtml } from '../../shared/dom.js';

const profileValue = (value) => escapeHtml(value || 'Не указано');

export const renderProfilePage = (state) => {
  const user = state.user;

  if (state.isLoading && !user) {
    return `
      <section class="profile-page">
        <div class="profile-card profile-card--loading">Загружаем профиль...</div>
      </section>
    `;
  }

  if (!user) {
    return `
      <section class="profile-page">
        <div class="profile-card">
          <h1>Профиль недоступен</h1>
          <p class="message is-error">${escapeHtml(state.message)}</p>
          <button class="button button--primary" data-action="go-auth" type="button">Вернуться ко входу</button>
        </div>
      </section>
    `;
  }

  return `
    <section class="profile-page" aria-labelledby="profile-title">
      <div class="profile-hero">
        <p class="eyebrow">Личный кабинет</p>
        <h1 id="profile-title">${profileValue(user.first_name)}, добро пожаловать!</h1>
        <p>Профиль уже подключен к API. Здесь удобно наращивать интерфейсы записей, услуг, отзывов и настроек аккаунта.</p>
        <div class="profile-actions">
          <button class="button button--primary" data-action="refresh-profile" type="button">Обновить профиль</button>
          <button class="button button--secondary" data-action="logout" type="button">Выйти</button>
        </div>
      </div>

      <article class="profile-card">
        <div class="avatar" aria-hidden="true">${profileValue(user.first_name).slice(0, 1)}</div>
        <dl class="profile-list">
          <div><dt>Email</dt><dd>${profileValue(user.email)}</dd></div>
          <div><dt>Телефон</dt><dd>${profileValue(user.phone_number)}</dd></div>
          <div><dt>Роль</dt><dd>${profileValue(user.role)}</dd></div>
          <div><dt>Фамилия</dt><dd>${profileValue(user.last_name)}</dd></div>
        </dl>
      </article>
    </section>
  `;
};
