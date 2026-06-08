import { renderAuthPage } from './features/auth/view.js';
import { submitAuth } from './features/auth/controller.js';
import { renderProfilePage } from './features/profile/view.js';
import { loadProfile } from './features/profile/controller.js';
import { qs } from './shared/dom.js';
import { clearAccessToken, getAccessToken } from './shared/storage.js';

const appRoot = qs('#app-root');

const state = {
  view: getAccessToken() ? 'profile' : 'auth',
  authMode: 'login',
  isLoading: false,
  message: 'Заполните форму, чтобы продолжить в личный профиль.',
  messageType: '',
  user: null,
};

const setState = (patch) => {
  Object.assign(state, patch);
  renderApp();
};

const showAuth = (message = 'Заполните форму, чтобы продолжить в личный профиль.') => {
  history.replaceState(null, '', '#auth');
  setState({ view: 'auth', user: null, message, messageType: '' });
};

const showProfile = async (message = 'Профиль открыт.') => {
  history.replaceState(null, '', '#profile');
  setState({ view: 'profile', isLoading: true, message, messageType: '' });

  try {
      const user = await loadProfile();
      setState({ user, isLoading: false, message, messageType: 'is-success' });
    } catch (error) {
      clearAccessToken();
      setState({
        view: 'auth',
        user: null,
        isLoading: false,
        message: error.message,
        messageType: 'is-error',
      });
    }
};

function renderApp() {
  appRoot.innerHTML = state.view === 'profile' ? renderProfilePage(state) : renderAuthPage(state);
};

appRoot.addEventListener('click', (event) => {
  const authModeButton = event.target.closest('[data-auth-mode]');
  const action = event.target.closest('[data-action]')?.dataset.action;

  if (authModeButton) {
    setState({
      authMode: authModeButton.dataset.authMode,
      message: 'Заполните форму, чтобы продолжить в личный профиль.',
      messageType: '',
    });
    return;
  }

  if (action === 'logout') {
    clearAccessToken();
    showAuth('Вы вышли из профиля. Можно войти снова.');
  }

  if (action === 'refresh-profile') {
    showProfile('Данные профиля обновлены.');
  }

  if (action === 'go-auth') {
    showAuth();
  }
});

appRoot.addEventListener('submit', async (event) => {
  event.preventDefault();

  setState({ isLoading: true, message: 'Отправляем JSON на backend...', messageType: '' });

  try {
    const mode = await submitAuth(event.target);
    await showProfile(mode === 'login' ? 'Вход выполнен.' : 'Регистрация завершена.');
  } catch (error) {
    setState({ isLoading: false, message: error.message, messageType: 'is-error' });
  }
});

const syncRoute = () => {
  if (location.hash === '#profile' && getAccessToken()) {
    showProfile('Сессия найдена, загружаем профиль.');
    return;
  }

  if (location.hash === '#profile' && !getAccessToken()) {
    showAuth('Сначала войдите или зарегистрируйтесь, чтобы открыть профиль.');
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
