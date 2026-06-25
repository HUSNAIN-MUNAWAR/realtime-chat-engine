# Screenshots

The committed portfolio screenshot is:

```text
docs/screenshots/portfolio-overview.png
```

Run the app first:

```bash
docker compose up --build
```

Then generate screenshots:

```bash
make screenshots
```

The Playwright script saves landing, login, register, chat, admin, load-tests, observability, and mlops screenshots from the real running frontend. It does not use mock screenshots.

For frontend-only verification without Docker, run:

```bash
cd frontend
npm ci
npm run build
npm start
npx playwright screenshot --browser=chromium --viewport-size=1440,1100 --full-page http://localhost:3000 ../docs/screenshots/portfolio-overview.png
```
