import { test } from '@playwright/test';

const pages = [
  ['landing', '/'],
  ['login', '/login'],
  ['register', '/register'],
  ['chat', '/app'],
  ['admin', '/app/admin'],
  ['load-tests', '/app/load-tests'],
  ['observability', '/app/observability'],
  ['mlops', '/app/mlops']
];

const user = {
  id: 'user-admin',
  email: 'admin@example.com',
  username: 'admin',
  role: 'admin'
};

const rooms = [
  { id: 'room-platform', name: 'platform-war-room', room_type: 'channel', workspace_id: 'workspace-prod' },
  { id: 'room-incidents', name: 'incident-response', room_type: 'channel', workspace_id: 'workspace-prod' },
  { id: 'room-product', name: 'product-updates', room_type: 'channel', workspace_id: 'workspace-prod' }
];

const messages = [
  {
    id: 'msg-001',
    room_id: 'room-platform',
    sender_id: 'user-admin',
    sender_username: 'admin',
    content: 'Redis fanout is healthy across all gateway replicas. p95 ack latency is holding under 42ms.',
    risk_label: 'clean',
    risk_score: 0.03,
    created_at: '2026-06-25T16:20:00Z'
  },
  {
    id: 'msg-002',
    room_id: 'room-platform',
    sender_id: 'user-demo',
    sender_username: 'demo',
    content: 'Load test shard 04 joined 10,000 virtual users and is publishing one message per user per second.',
    risk_label: 'clean',
    risk_score: 0.07,
    created_at: '2026-06-25T16:22:00Z'
  },
  {
    id: 'msg-003',
    room_id: 'room-platform',
    sender_id: 'user-ops',
    sender_username: 'ops-lead',
    content: 'A suspicious message was scored for review and queued for admin moderation with the full audit trail.',
    risk_label: 'review',
    risk_score: 0.62,
    created_at: '2026-06-25T16:25:00Z'
  },
  {
    id: 'msg-004',
    room_id: 'room-platform',
    sender_id: 'user-admin',
    sender_username: 'admin',
    content: 'Thread reply confirms delivery and read receipts are persisted for the parent message.',
    risk_label: 'clean',
    risk_score: 0.02,
    parent_message_id: 'msg-001',
    created_at: '2026-06-25T16:27:00Z'
  }
];

async function seedDocumentationState(page: import('@playwright/test').Page) {
  await page.addInitScript(({ user }) => {
    window.localStorage.setItem('chat_token', 'documentation-jwt');
    window.localStorage.setItem('chat_user', JSON.stringify(user));

    class MockWebSocket {
      static CONNECTING = 0;
      static OPEN = 1;
      static CLOSING = 2;
      static CLOSED = 3;
      readyState = MockWebSocket.OPEN;
      onopen: ((event: Event) => void) | null = null;
      onmessage: ((event: MessageEvent) => void) | null = null;
      onclose: ((event: CloseEvent) => void) | null = null;

      constructor() {
        window.setTimeout(() => this.onopen?.(new Event('open')), 25);
      }

      send() {}

      close() {
        this.readyState = MockWebSocket.CLOSED;
        window.setTimeout(() => this.onclose?.(new CloseEvent('close')), 10);
      }
    }

    window.WebSocket = MockWebSocket as unknown as typeof WebSocket;
  }, { user });

  await page.route('**/api/v1/rooms', async (route) => route.fulfill({ json: rooms }));
  await page.route('**/api/v1/users', async (route) => route.fulfill({
    json: [
      user,
      { id: 'user-demo', email: 'demo@example.com', username: 'demo', role: 'member' },
      { id: 'user-ops', email: 'ops@example.com', username: 'ops-lead', role: 'member' }
    ]
  }));
  await page.route('**/api/v1/messages/room-platform', async (route) => route.fulfill({
    json: { items: messages, next_cursor: null }
  }));
  await page.route('**/api/v1/workspaces', async (route) => route.fulfill({
    json: [{ id: 'workspace-prod', name: 'Production Workspace', owner_id: user.id }]
  }));
  await page.route('**/api/v1/admin/stats', async (route) => route.fulfill({
    json: {
      users: 12842,
      rooms: 348,
      total_messages: 982441,
      active_connections_local: 24176,
      active_rooms_local: 176,
      risky_messages: 19,
      system: { process_rss_mb: 612, system_memory_percent: 64 }
    }
  }));
  await page.route('**/api/v1/admin/risky-messages', async (route) => route.fulfill({
    json: [
      { id: 'risk-1', room_id: 'room-platform', content: 'urgent money scam send password now', risk_label: 'risky', risk_score: 0.92 },
      { id: 'risk-2', room_id: 'room-incidents', content: 'Possible credential-sharing attempt detected in a workspace room.', risk_label: 'review', risk_score: 0.68 }
    ]
  }));
  await page.route('**/api/v1/admin/load-test-runs', async (route) => route.fulfill({
    json: [
      { id: 'run-100k', name: '100k distributed websocket simulation', status: 'completed', users: 100000, rooms: 1000, message_rate: 1 },
      { id: 'run-10k', name: '10k local stress profile', status: 'completed', users: 10000, rooms: 250, message_rate: 0.2 }
    ]
  }));
  await page.route('**/api/v1/mlops/model', async (route) => route.fulfill({
    json: { version: 'nb-risk-v1', labels: ['clean', 'risky'], training_rows: 15, artifact: 'mlops/models/current/risk_model.json' }
  }));
  await page.route('**/api/v1/mlops/risk-score', async (route) => route.fulfill({
    json: { label: 'risky', score: 0.92, model_version: 'nb-risk-v1', latency_ms: 1.8 }
  }));
}

test.describe('documentation screenshots', () => {
  for (const [name, path] of pages) {
    test(`screenshot ${name}`, async ({ page }) => {
      await seedDocumentationState(page);
      await page.goto(`http://localhost:3000${path}`);
      if (name === 'register') {
        await page.getByPlaceholder('Email').fill('new.member@example.com');
        await page.getByPlaceholder('Username').fill('new-member');
        await page.getByPlaceholder('Password').fill('StrongPass123!');
      }
      if (name === 'chat') {
        await page.getByText('Open thread').first().click();
      }
      if (name === 'mlops') {
        await page.getByRole('button', { name: 'Score text' }).click();
      }
      await page.waitForTimeout(300);
      await page.screenshot({ path: `../docs/screenshots/${name}.png`, fullPage: true });
    });
  }
});
