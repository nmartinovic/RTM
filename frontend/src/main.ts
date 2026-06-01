import { apiBaseUrl } from './config';

type NavItem = {
  path: string;
  label: string;
  description: string;
};

const navItems: NavItem[] = [
  {
    path: '/dashboard',
    label: 'Dashboard',
    description: 'Connection health, task hygiene, and review workload summaries.',
  },
  {
    path: '/uploads',
    label: 'Uploads',
    description: 'Drop source documents or pasted text for backend extraction.',
  },
  {
    path: '/review-queues',
    label: 'Review queues',
    description: 'Approve, reject, edit, or merge task and action proposals.',
  },
  {
    path: '/audit',
    label: 'Audit',
    description: 'Review processing runs, applied RTM changes, and operator actions.',
  },
  {
    path: '/settings',
    label: 'Settings',
    description: 'Manage browser-safe dashboard preferences and backend endpoint details.',
  },
];

const routeTitles: Record<string, string> = {
  '/dashboard': 'Review RTM work before anything is applied',
  '/uploads': 'Uploads workspace',
  '/review-queues': 'Review queues workspace',
  '/audit': 'Audit workspace',
  '/settings': 'Browser-safe configuration',
};

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Missing #root element');
}

const root = rootElement;
let backendStatus: 'checking' | 'online' | 'offline' = 'checking';
type RtmConnectionStatus = 'checking' | 'connected' | 'disconnected' | 'auth-required' | 'error';
type RtmStatusResponse = {
  connected: boolean;
  user: {
    username: string;
    fullname: string;
  } | null;
  perms: string | null;
};
type RtmSyncResponse = {
  list_count: number;
  active_task_count: number;
};
let rtmStatus: RtmConnectionStatus = 'checking';
let rtmUserLabel = '';
let rtmStatusMessage = 'Checking RTM connection.';
let rtmListCount = '—';
let rtmTaskCount = '—';
let rtmSyncMessage = 'No RTM sync has run yet.';

function getCurrentRoute() {
  const route = window.location.hash.replace(/^#/, '') || '/dashboard';
  return navItems.some((item) => item.path === route) ? route : '/dashboard';
}

function render() {
  const currentRoute = getCurrentRoute();
  const currentNav = navItems.find((item) => item.path === currentRoute) ?? navItems[0];

  root.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar" aria-label="Primary navigation">
        <div class="brand-block">
          <span class="brand-mark">RTM</span>
          <div>
            <p class="eyebrow">AI Task Organizer</p>
            <h1>Static dashboard</h1>
          </div>
        </div>
        <nav class="nav-list">
          ${navItems
            .map(
              (item) => `
                <a class="nav-link${item.path === currentRoute ? ' active' : ''}" href="#${item.path}">
                  ${item.label}
                </a>`,
            )
            .join('')}
        </nav>
      </aside>
      <main class="content-panel">${renderRoute(currentRoute, currentNav)}</main>
    </div>
  `;
}

function renderRoute(route: string, navItem: NavItem) {
  if (route === '/dashboard') {
    const statusLabel = backendStatus === 'online' ? 'Online' : backendStatus === 'offline' ? 'Offline' : 'Checking';
    const statusText =
      backendStatus === 'online'
        ? 'Backend health check passed.'
        : backendStatus === 'offline'
          ? 'Backend health check failed.'
          : 'Checking backend health.';

    return `
      <section class="page-stack" aria-labelledby="dashboard-title">
        ${pageHeader(
          'Dashboard',
          routeTitles[route],
          'This shell is safe for static hosting: it only reads browser-safe configuration and delegates secret-bearing RTM and Gemma work to the backend API.',
        )}
        <div class="status-card">
          <div>
            <p class="eyebrow">Backend API</p>
            <h2 id="dashboard-title">Configured endpoint</h2>
          </div>
          <div class="status-stack">
            <span class="status-pill ${backendStatus}" aria-live="polite">${statusLabel}</span>
            <span>${statusText}</span>
            <code>${apiBaseUrl}</code>
          </div>
        </div>
        <div class="status-card">
          <div>
            <p class="eyebrow">Remember The Milk</p>
            <h2>Account connection</h2>
          </div>
          <div class="status-stack">
            <span class="status-pill ${rtmStatus}" aria-live="polite">${rtmStatusLabel()}</span>
            <span>${escapeHtml(rtmStatusMessage)}</span>
            ${rtmUserLabel ? `<code>${escapeHtml(rtmUserLabel)}</code>` : ''}
            <button class="primary-button" type="button" data-action="connect-rtm">Connect RTM</button>
            <button class="secondary-button" type="button" data-action="sync-rtm">Sync read-only</button>
          </div>
        </div>
        <div class="metric-grid" aria-label="Queue summaries">
          ${[
            ['RTM lists', rtmListCount, rtmSyncMessage],
            ['Active tasks', rtmTaskCount, 'Incomplete RTM tasks returned by read-only sync'],
            ['Recent uploads', '—', 'No upload API data loaded yet'],
          ]
            .map(
              ([label, value, helper]) => `
                <article class="metric-card">
                  <p>${label}</p>
                  <strong>${value}</strong>
                  <span>${helper}</span>
                </article>`,
            )
            .join('')}
        </div>
      </section>`;
  }

  if (route === '/settings') {
    return `
      <section class="page-stack" aria-labelledby="settings-title">
        ${pageHeader('Settings', routeTitles[route], navItem.description)}
        <div class="placeholder-card">
          <h2 id="settings-title">Active API base URL</h2>
          <code>${apiBaseUrl}</code>
          <p>Do not place RTM shared secrets, Gemma keys, database URLs, session signing keys, or long-lived tokens in frontend environment variables.</p>
        </div>
      </section>`;
  }

  return `
    <section class="page-stack" aria-labelledby="${route.slice(1)}-title">
      ${pageHeader(navItem.label, routeTitles[route], navItem.description)}
      <div class="placeholder-card">
        <h2 id="${route.slice(1)}-title">Placeholder route ready</h2>
        <p>The route and layout are in place. API-backed forms, tables, and workflows can be added here without changing the static hosting model.</p>
      </div>
    </section>`;
}

async function checkBackendHealth() {
  backendStatus = 'checking';
  render();

  try {
    const response = await fetch(`${apiBaseUrl}/health`, {
      cache: 'no-store',
      mode: 'cors',
    });
    backendStatus = response.ok ? 'online' : 'offline';
  } catch {
    backendStatus = 'offline';
  }

  render();
}

async function checkRtmStatus() {
  rtmStatus = 'checking';
  rtmStatusMessage = 'Checking RTM connection.';
  rtmUserLabel = '';
  render();

  try {
    const response = await fetch(`${apiBaseUrl}/api/rtm/status`, {
      cache: 'no-store',
      credentials: 'include',
      mode: 'cors',
    });

    if (response.status === 401) {
      rtmStatus = 'auth-required';
      rtmStatusMessage = 'Sign in to the backend before connecting RTM.';
      render();
      return;
    }

    if (!response.ok) {
      throw new Error('RTM status check failed');
    }

    const status = (await response.json()) as RtmStatusResponse;
    rtmStatus = status.connected ? 'connected' : 'disconnected';
    rtmUserLabel = status.user?.fullname || status.user?.username || '';
    rtmStatusMessage = status.connected ? 'RTM token is stored on the backend.' : 'RTM is not connected yet.';
  } catch {
    rtmStatus = 'error';
    rtmStatusMessage = 'Unable to load RTM connection status.';
  }

  render();
}

async function connectRtm() {
  rtmStatusMessage = 'Opening RTM authorization.';
  render();

  try {
    const response = await fetch(`${apiBaseUrl}/api/rtm/connect`, {
      method: 'POST',
      credentials: 'include',
      mode: 'cors',
    });

    if (response.status === 401) {
      rtmStatus = 'auth-required';
      rtmStatusMessage = 'Sign in to the backend before connecting RTM.';
      render();
      return;
    }

    if (!response.ok) {
      throw new Error('RTM authorization URL failed');
    }

    const payload = (await response.json()) as { authorization_url: string };
    window.location.href = payload.authorization_url;
  } catch {
    rtmStatus = 'error';
    rtmStatusMessage = 'Unable to start RTM authorization.';
    render();
  }
}

async function syncRtmReadOnly() {
  rtmSyncMessage = 'Syncing RTM lists and incomplete tasks.';
  render();

  try {
    const response = await fetch(`${apiBaseUrl}/api/rtm/sync`, {
      cache: 'no-store',
      credentials: 'include',
      mode: 'cors',
    });

    if (response.status === 401) {
      rtmSyncMessage = 'Sign in to the backend before syncing RTM.';
      render();
      return;
    }

    if (response.status === 409) {
      rtmSyncMessage = 'Connect RTM before running read-only sync.';
      render();
      return;
    }

    if (!response.ok) {
      throw new Error('RTM sync failed');
    }

    const payload = (await response.json()) as RtmSyncResponse;
    rtmListCount = String(payload.list_count);
    rtmTaskCount = String(payload.active_task_count);
    rtmSyncMessage = 'Read-only sync completed.';
  } catch {
    rtmSyncMessage = 'Unable to sync RTM data.';
  }

  render();
}

function rtmStatusLabel() {
  if (rtmStatus === 'connected') {
    return 'Connected';
  }
  if (rtmStatus === 'auth-required') {
    return 'Sign in';
  }
  if (rtmStatus === 'error') {
    return 'Error';
  }
  if (rtmStatus === 'disconnected') {
    return 'Disconnected';
  }
  return 'Checking';
}

function escapeHtml(value: string) {
  return value.replace(/[&<>"']/g, (character) => {
    const entities: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    };
    return entities[character];
  });
}

function pageHeader(eyebrow: string, title: string, description: string) {
  return `
    <header class="page-header">
      <p class="eyebrow">${eyebrow}</p>
      <h2>${title}</h2>
      <p>${description}</p>
    </header>`;
}

window.addEventListener('hashchange', render);
root.addEventListener('click', (event) => {
  const target = event.target;
  if (target instanceof HTMLElement && target.dataset.action === 'connect-rtm') {
    void connectRtm();
  }
  if (target instanceof HTMLElement && target.dataset.action === 'sync-rtm') {
    void syncRtmReadOnly();
  }
});

if (!window.location.hash) {
  window.location.hash = '#/dashboard';
} else {
  render();
}

void checkBackendHealth();
void checkRtmStatus();
