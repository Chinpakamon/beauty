import { renderAuthPage } from './features/auth/view.js';
import { submitAuth } from './features/auth/controller.js';
import { renderDirectoryPage, renderProfilePage } from './features/profile/view.js';
import { loadProfile, updateProfile } from './features/profile/controller.js';
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

const showPrivateView = async (view = 'profile', message = 'Профиль открыт.') => {
  history.replaceState(null, '', `#${view}`);
  setState({ view, isLoading: true, message, messageType: '' });

  try {
    const user = await loadProfile();
    setState({ user, isLoading: false, message, messageType: 'is-success' });
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
      setState({ user, isLoading: false, message: 'Профиль успешно обновлен.', messageType: 'is-success' });
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
