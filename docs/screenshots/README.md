# Screenshots

The committed portfolio gallery contains:

```text
docs/screenshots/landing.png
docs/screenshots/login.png
docs/screenshots/register.png
docs/screenshots/chat.png
docs/screenshots/admin.png
docs/screenshots/load-tests.png
docs/screenshots/observability.png
docs/screenshots/mlops.png
```

Run the app first:

```bash
docker compose up --build
```

Then generate screenshots:

```bash
make screenshots
```

The Playwright script saves landing, login, register, chat, admin, load-tests, observability, and mlops screenshots from the running frontend routes. For live backend-backed captures, start the full Docker stack first so the same product surfaces connect to FastAPI, Redis, PostgreSQL, Prometheus, and Grafana.

For frontend-only verification without Docker, run:

```bash
cd frontend
npm ci
npm run build
npm start
npx playwright test tests/screenshots.spec.ts
```
