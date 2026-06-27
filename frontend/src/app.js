import { renderAuthPage } from './features/auth/view.js';
import { submitAuth } from './features/auth/controller.js';
import { renderDirectoryPage, renderProfilePage } from './features/profile/view.js';
import { listServices, listSpecialists, loadProfile, updateProfile } from './features/profile/controller.js';
import { qs } from './shared/dom.js';
import { clearAccessToken, getAccessToken } from './shared/storage.js';

const appRoot = qs('#app-root');

const DEFAULT_AUTH_MESSAGE = 'Заполните форму, чтобы продолжить';
const PRIVATE_VIEWS = new Set(['profile', 'specialists', 'services']);

const state = {
  view: getAccessToken() ? 'profile' : 'auth',
  authMode: 'login',
  isLoading: false,
  message: DEFAULT_AUTH_MESSAGE,
  messageType: '',
  user: null,
  isEditingProfile: false,
  specialists: null,
  services: null,
  specialistFilters: { order_by: 'FIRST_NAME_ASC', limit: 20, offset: 0 },
  serviceFilters: { order_by: 'CREATED_AT_DESC', limit: 20, offset: 0 },
};

const setState = (patch) => {
  Object.assign(state, patch);
  renderApp();
};

const normalizeHash = () => location.hash.replace('#', '') || 'auth';

const showAuth = (message = DEFAULT_AUTH_MESSAGE) => {
  history.replaceState(null, '', '/');
  setState({ view: 'auth', user: null, message, messageType: '' });
};

const loadDirectory = async (view) => {
  if (view === 'specialists') return { specialists: await listSpecialists() };
  if (view === 'services') return { services: await listServices() };
  return {};
};

const showPrivateView = async (view = 'profile', message = 'Профиль открыт.') => {
  history.replaceState(null, '', `#${view}`);
  setState({ view, isLoading: true, message, messageType: '', isEditingProfile: false });

  try {
    const user = await loadProfile();
    const directoryPatch = await loadDirectory(view);
    setState({ user, ...directoryPatch, isLoading: false, message, messageType: 'is-success' });
  } catch (error) {
    clearAccessToken();
    history.replaceState(null, '', '/');
    setState({
      view: 'auth',
      user: null,
      isLoading: false,
      message: error.message,
      messageType: 'is-error',
    });
  }
};

const showProfile = (message = 'Профиль открыт.') => showPrivateView('profile', message);

function renderApp() {
  if (state.view === 'profile') {
    appRoot.innerHTML = renderProfilePage(state);
    return;
  }

  if (state.view === 'specialists' || state.view === 'services') {
    appRoot.innerHTML = renderDirectoryPage(state);
    return;
  }

  appRoot.innerHTML = renderAuthPage(state);
}

appRoot.addEventListener('click', (event) => {
  const authModeButton = event.target.closest('[data-auth-mode]');
  const action = event.target.closest('[data-action]')?.dataset.action;

  if (authModeButton) {
    setState({
      authMode: authModeButton.dataset.authMode,
      message: DEFAULT_AUTH_MESSAGE,
      messageType: '',
    });
    return;
  }

  if (action === 'logout') {
    clearAccessToken();
    showAuth('Вы вышли из профиля. Можно войти снова.');
  }

  if (action === 'edit-profile') {
    setState({ isEditingProfile: true, message: 'Теперь данные можно изменить.', messageType: '' });
  }

  if (action === 'cancel-edit-profile') {
    setState({ isEditingProfile: false, message: 'Изменения отменены.', messageType: '' });
  }

  if (action === 'refresh-profile') {
    showPrivateView(state.view, 'Данные профиля обновлены.');
  }
});

appRoot.addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.target;

  if (form.matches('[data-profile-form]')) {
    setState({ isLoading: true, message: 'Сохраняем профиль...', messageType: '' });

    try {
      const user = await updateProfile(state.user.id, form);
      setState({ user, isLoading: false, isEditingProfile: false, message: 'Профиль успешно обновлен.', messageType: 'is-success' });
    } catch (error) {
      setState({ isLoading: false, message: error.message, messageType: 'is-error' });
    }
    return;
  }

  if (form.matches('[data-list-form]')) {
    const type = form.dataset.listForm;
    const values = Object.fromEntries(new FormData(form).entries());
    setState({ isLoading: true, message: 'Загружаем список...', messageType: '' });

  try {
    if (type === 'specialists') {
      const specialists = await listSpecialists(form);
      setState({ specialists, specialistFilters: values, isLoading: false, message: `Найдено специалистов: ${specialists.total}.`, messageType: 'is-success' });
    } else {
      const services = await listServices(form);
      setState({ services, serviceFilters: values, isLoading: false, message: `Найдено услуг: ${services.total}.`, messageType: 'is-success' });
    }    
  } catch (error) {
    setState({ isLoading: false, message: error.message, messageType: 'is-error' });
  }
  return;
}

  setState({ isLoading: true, message: 'Отправляем JSON на backend...', messageType: '' });

  try {
    const mode = await submitAuth(form);
    await showProfile(mode === 'login' ? 'Вход выполнен.' : 'Регистрация завершена.');
  } catch (error) {
    setState({ isLoading: false, message: error.message, messageType: 'is-error' });
  }
});

const syncRoute = () => {
  const route = normalizeHash();

  if (PRIVATE_VIEWS.has(route) && getAccessToken()) {
    showPrivateView(route, route === 'profile' ? 'Сессия найдена, загружаем профиль.' : 'Открываем раздел из профиля.');
    return;
  }

  if (PRIVATE_VIEWS.has(route) && !getAccessToken()) {
    showAuth('Сначала войдите или зарегистрируйтесь, чтобы открыть этот раздел.');
    return;
  }

  if (getAccessToken()) {
    showProfile('Сессия найдена, загружаем профиль.');
    return;
  }

  renderApp();
};

window.addEventListener('hashchange', syncRoute);
syncRoute();
