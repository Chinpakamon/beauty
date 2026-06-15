import { escapeHtml } from '../../shared/dom.js';

const profileValue = (value) => escapeHtml(value || 'Не указано');
const inputValue = (value) => escapeHtml(value || '');

const profileShortcutTemplate = ({ href, icon, title, text }) => `
  <a class="profile-shortcut" href="${escapeHtml(href)}">
    <span class="profile-shortcut__icon" aria-hidden="true">${escapeHtml(icon)}</span>
    <span>
      <strong>${escapeHtml(title)}</strong>
      <small>${escapeHtml(text)}</small>
    </span>
  </a>
`;

const directoryPageTemplate = ({ title, text, cards }) => `
  <section class="directory-page" aria-labelledby="directory-title">
    <div class="directory-hero profile-card">
      <p class="eyebrow">Каталог</p>
      <h1 id="directory-title">${escapeHtml(title)}</h1>
      <p>${escapeHtml(text)}</p>
      <div class="profile-actions">
        <a class="button button--primary" href="#profile">Вернуться в профиль</a>
        <button class="button button--secondary" data-action="refresh-profile" type="button">Обновить профиль</button>
      </div>
    </div>
    <div class="directory-grid">
      ${cards
        .map(
          (card) => `
            <article class="profile-card directory-card">
              <span class="profile-shortcut__icon" aria-hidden="true">${escapeHtml(card.icon)}</span>
              <h2>${escapeHtml(card.title)}</h2>
              <p>${escapeHtml(card.text)}</p>
            </article>
          `,
        )
        .join('')}
    </div>
  </section>
`;

export const renderDirectoryPage = (state) => {
  if (state.view === 'specialists') {
    return directoryPageTemplate({
      title: 'Специалисты',
      text: 'Здесь можно развить список мастеров, фильтры по направлениям и переход к записи.',
      cards: [
        { icon: '💇‍♀️', title: 'Парикмахеры', text: 'Стрижки, окрашивание и уходовые процедуры.' },
        { icon: '💅', title: 'Nail-мастера', text: 'Маникюр, педикюр и дизайн ногтей.' },
        { icon: '🧖‍♀️', title: 'Косметологи', text: 'Уход за кожей и персональные консультации.' },
      ],
    });
  }

  return directoryPageTemplate({
    title: 'Услуги',
    text: 'Здесь можно показать доступные услуги сайта, цены, длительность и кнопку записи.',
    cards: [
      { icon: '✨', title: 'Уход', text: 'Комплексные beauty-процедуры для лица и тела.' },
      { icon: '🎨', title: 'Окрашивание', text: 'Подбор образа, цвета и техники.' },
      { icon: '📅', title: 'Запись', text: 'Быстрый переход к бронированию удобного времени.' },
    ],
  });
};

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
          <a class="button button--primary" href="/">Вернуться ко входу</a>
        </div>
      </section>
    `;
  }

  return `
    <section class="profile-page" aria-labelledby="profile-title">
      <div class="profile-hero">
        <p class="eyebrow">Личный кабинет</p>
        <h1 id="profile-title">${profileValue(user.first_name)}, добро пожаловать!</h1>
        <p>Редактируйте данные профиля прямо в личном кабинете и быстро переходите к специалистам или услугам сайта.</p>
        <nav class="profile-shortcuts" aria-label="Быстрые переходы">
          ${profileShortcutTemplate({ href: '#specialists', icon: '👩‍🎨', title: 'Специалисты', text: 'Найти мастера' })}
          ${profileShortcutTemplate({ href: '#services', icon: '💎', title: 'Услуги', text: 'Выбрать процедуру' })}
        </nav>
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

        <form class="profile-form" data-profile-form>
          <h2>Редактировать профиль</h2>
          <div class="form-row">
            <label class="field">Имя<input name="first_name" type="text" autocomplete="given-name" value="${inputValue(user.first_name)}" required /></label>
            <label class="field">Фамилия<input name="last_name" type="text" autocomplete="family-name" value="${inputValue(user.last_name)}" /></label>
          </div>
          <label class="field">Телефон<input name="phone_number" type="tel" autocomplete="tel" value="${inputValue(user.phone_number)}" required /></label>
          <button class="auth-submit" type="submit" ${state.isLoading ? 'disabled' : ''}>${state.isLoading ? 'Сохраняем...' : 'Сохранить изменения'}</button>
          <p class="message ${state.messageType}" role="status" aria-live="polite">${escapeHtml(state.message)}</p>
        </form>
      </article>
    </section>
  `;
};
