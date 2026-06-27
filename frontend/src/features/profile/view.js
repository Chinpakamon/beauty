import { escapeHtml } from '../../shared/dom.js';

const profileValue = (value) => escapeHtml(value || 'Не указано');
const inputValue = (value) => escapeHtml(value || '');
const selected = (current, value) => current === value ? 'selected' : '';

const sidebarTemplate = (active) => `
  <aside class="profile-sidebar profile-card" aria-label="Разделы профиля">
    <a class="logo" href="#profile"><span class="logo__mark">B</span><span>Beauty</span></a>
    <nav class="profile-menu">
      ${[
        ['profile', 'Главная'],
        ['specialists', 'Специалисты'],
        ['services', 'Услуги'],
      ].map(([view, label]) => `<a class="profile-menu__link ${active === view ? 'is-active' : ''}" href="#${view}">${label}</a>`).join('')}
    </nav>
  </aside>
`;

export const renderDirectoryPage = (state) => {
  const isSpecialists = state.view === 'specialists';
  const list = isSpecialists ? state.specialists : state.services;
  const filters = isSpecialists ? state.specialistFilters : state.serviceFilters;

  return `
    <section class="profile-layout">
      ${sidebarTemplate(state.view)}
      <main class="profile-content directory-page" aria-labelledby="directory-title">
        <div class="profile-card directory-hero">
          <p class="eyebrow">Каталог</p>
          <h1 id="directory-title">${isSpecialists ? 'Специалисты' : 'Услуги'}</h1>
          <p>${isSpecialists ? 'Список мастеров загружается из ручки списка пользователей с фильтром по роли MASTER.' : 'Список услуг загружается из ручки списка услуг с доступными фильтрами и сортировками.'}</p>
        </div>
        <form class="profile-card directory-filters" data-list-form="${isSpecialists ? 'specialists' : 'services'}">
          <div class="form-row">
            ${isSpecialists ? `
              <label class="field">Имя<input name="first_name" value="${inputValue(filters.first_name)}" placeholder="Анна" /></label>
              <label class="field">Фамилия<input name="last_name" value="${inputValue(filters.last_name)}" placeholder="Иванова" /></label>
              <label class="field">Email<input name="email" type="email" value="${inputValue(filters.email)}" placeholder="master@example.com" /></label>
              <label class="field">Сортировка<select name="order_by">
                <option value="FIRST_NAME_ASC" ${selected(filters.order_by, 'FIRST_NAME_ASC')}>Имя ↑</option>
                <option value="FIRST_NAME_DESC" ${selected(filters.order_by, 'FIRST_NAME_DESC')}>Имя ↓</option>
                <option value="LAST_NAME_ASC" ${selected(filters.order_by, 'LAST_NAME_ASC')}>Фамилия ↑</option>
                <option value="EMAIL_ASC" ${selected(filters.order_by, 'EMAIL_ASC')}>Email ↑</option>
              </select></label>
            ` : `
              <label class="field">ID мастера<input name="master_id" type="number" min="1" value="${inputValue(filters.master_id)}" /></label>
              <label class="field">ID типа услуги<input name="service_type_id" type="number" min="1" value="${inputValue(filters.service_type_id)}" /></label>
              <label class="field">Мин. цена<input name="min_price" type="number" min="0" value="${inputValue(filters.min_price)}" /></label>
              <label class="field">Макс. цена<input name="max_price" type="number" min="0" value="${inputValue(filters.max_price)}" /></label>
              <label class="field">Активность<select name="is_active"><option value="">Все</option><option value="true" ${selected(filters.is_active, 'true')}>Активные</option><option value="false" ${selected(filters.is_active, 'false')}>Неактивные</option></select></label>
              <label class="field">Сортировка<select name="order_by"><option value="CREATED_AT_DESC" ${selected(filters.order_by, 'CREATED_AT_DESC')}>Новые</option><option value="PRICE_ASC" ${selected(filters.order_by, 'PRICE_ASC')}>Цена ↑</option><option value="PRICE_DESC" ${selected(filters.order_by, 'PRICE_DESC')}>Цена ↓</option><option value="DURATION_ASC" ${selected(filters.order_by, 'DURATION_ASC')}>Длительность ↑</option><option value="DURATION_DESC" ${selected(filters.order_by, 'DURATION_DESC')}>Длительность ↓</option></select></label>
            `}
            <label class="field">Лимит<input name="limit" type="number" min="1" max="100" value="${inputValue(filters.limit || 20)}" /></label>
            <label class="field">Смещение<input name="offset" type="number" min="0" value="${inputValue(filters.offset || 0)}" /></label>
          </div>
          <button class="auth-submit" type="submit" ${state.isLoading ? 'disabled' : ''}>Применить фильтры</button>
          <p class="message ${state.messageType}" role="status">${escapeHtml(state.message)}</p>
        </form>
        <div class="directory-list">
          ${(list?.data || []).map((item) => isSpecialists ? `
            <article class="profile-card directory-row"><h2>${profileValue(item.first_name)} ${profileValue(item.last_name)}</h2><p>${profileValue(item.email)} · ${profileValue(item.phone_number)}</p><span class="badge">${profileValue(item.role)}</span></article>
          ` : `
            <article class="profile-card directory-row"><h2>Услуга #${profileValue(item.id)}</h2><p>Мастер #${profileValue(item.master_id)} · Тип #${profileValue(item.service_type_id)} · ${profileValue(item.duration_minutes)} мин.</p><strong>${profileValue(item.price)} ₽</strong><span class="badge">${item.is_active ? 'Активна' : 'Неактивна'}</span><p>${profileValue(item.description)}</p></article>
          `).join('') || '<div class="profile-card">Ничего не найдено.</div>'}
        </div>
      </main>
    </section>
  `;
};

export const renderProfilePage = (state) => {
  const user = state.user;
  const editing = state.isEditingProfile;

  if (state.isLoading && !user) return `<section class="profile-page"><div class="profile-card profile-card--loading">Загружаем профиль...</div></section>`;
  if (!user) return `<section class="profile-page"><div class="profile-card"><h1>Профиль недоступен</h1><p class="message is-error">${escapeHtml(state.message)}</p><a class="button button--primary" href="/">Вернуться ко входу</a></div></section>`;

  return `
    <section class="profile-layout" aria-labelledby="profile-title">
      ${sidebarTemplate('profile')}
      <main class="profile-content">
        <article class="profile-card profile-main-card">
          <header class="profile-card__header">
            <div><p class="eyebrow">Личный кабинет</p><h1 id="profile-title">Моя информация</h1><p>Классическая форма профиля. Данные заблокированы до нажатия «Изменить данные».</p></div>
            <div class="profile-actions profile-actions--top">
              <button class="button button--primary" data-action="edit-profile" type="button" ${editing ? 'disabled' : ''}>Изменить данные</button>
              <button class="button button--secondary" data-action="logout" type="button">Выйти</button>
            </div>
          </header>
          <form class="profile-form" data-profile-form>
            <div class="avatar" aria-hidden="true">${profileValue(user.first_name).slice(0, 1)}</div>
            <div class="form-row">
              <label class="field">Имя<input name="first_name" type="text" autocomplete="given-name" value="${inputValue(user.first_name)}" required ${editing ? '' : 'disabled'} /></label>
              <label class="field">Фамилия<input name="last_name" type="text" autocomplete="family-name" value="${inputValue(user.last_name)}" ${editing ? '' : 'disabled'} /></label>
            </div>
            <label class="field">Email<input type="email" value="${inputValue(user.email)}" disabled /></label>
            <label class="field">Телефон<input name="phone_number" type="tel" autocomplete="tel" value="${inputValue(user.phone_number)}" required ${editing ? '' : 'disabled'} /></label>
            <label class="field">Роль<input value="${inputValue(user.role)}" disabled /></label>
            ${editing ? `<div class="profile-actions"><button class="button button--secondary" data-action="cancel-edit-profile" type="button">Отменить</button><button class="auth-submit" type="submit" ${state.isLoading ? 'disabled' : ''}>${state.isLoading ? 'Сохраняем...' : 'Сохранить'}</button></div>` : ''}
            <p class="message ${state.messageType}" role="status" aria-live="polite">${escapeHtml(state.message)}</p>
          </form>
        </article>
      </main>
    </section>
  `;
};
