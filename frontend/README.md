# QuantYield Frontend

Institutional fixed income analytics platform — React + Vite + Recharts.

## Tech Stack

| Layer      | Tech                                        |
| ---------- | ------------------------------------------- |
| Framework  | React 18                                    |
| Build      | Vite 5                                      |
| Routing    | React Router v6                             |
| Charts     | Recharts 2                                  |
| Icons      | Lucide React                                |
| Animations | Framer Motion                               |
| Fonts      | Inter · Space Grotesk · JetBrains Mono      |
| Auth       | Context API + localStorage                  |
| State      | React hooks (useState, useMemo, useContext) |

## Pages

- **/** — Landing / homepage (features, pricing, CTA)
- **/login** — Sign in page with demo credentials
- **/register** — Registration with plan selection and password strength
- **/app/dashboard** — KPI grid, yield curve, AI forecast, sector allocation, scenarios
- **/app/bonds** — Searchable bond universe with live detail panel (cash flows, KRD, spreads, total return)
- **/app/portfolios** — Portfolio cards, positions table, sector/rating/maturity charts, VaR, custom scenarios
- **/app/curves** — Full 4-model yield curve, Nelson-Siegel params, regime, historical comparison, custom builder
- **/app/analytics** — Quick pricer, duration approximation, benchmark spreads, rolling vol, yield history
- **/app/ml** — 5 ML models: Transformer forecaster, Regime classifier, GARCH, XGBoost credit, PCA factors

## Prerequisites

- **Node.js** 18+ (LTS recommended)
- **npm** 9+ (comes with Node)

## Quick Start

```bash
# 1. Install dependencies
npm install

# 2. Start development server (opens browser at http://localhost:3000)
npm run dev

# 3. Build for production
npm run build

# 4. Preview production build locally
npm run preview
```

## Demo Credentials

Any email + any password (8+ chars) will work. For quick access:

- **Email:** demo@quantyield.io
- **Password:** demo1234

Or use the "Use demo credentials" button on the login page.

## Project Structure

```
src/
├── main.jsx                  # Entry point
├── App.jsx                   # Router + providers
├── context/
│   ├── AuthContext.jsx        # Auth state + login/register/logout
│   └── ToastContext.jsx       # Global toast notifications
├── data/
│   └── mockData.js            # Mock API data (bonds, portfolios, curves, ML)
├── styles/
│   ├── globals.css            # CSS variables, reset, animations
│   └── components.css         # Sidebar, topbar, cards, tables, badges, etc.
├── components/
│   └── Layout/
│       └── AppLayout.jsx      # Sidebar + topbar shell
└── pages/
    ├── Landing.jsx            # Homepage
    ├── landing.css
    ├── Login.jsx              # Auth pages
    ├── Register.jsx
    ├── auth.css
    └── app/
        ├── Dashboard.jsx
        ├── Bonds.jsx
        ├── Portfolios.jsx
        ├── Curves.jsx
        ├── Analytics.jsx
        └── ML.jsx
```

## API Integration

The frontend is built against the QuantYield Django REST API. Replace `src/data/mockData.js` calls with real `fetch()` calls to:

```
Base URL: http://localhost:8000/api/v1/

GET    /bonds/                      List bonds
POST   /bonds/                      Create bond
GET    /bonds/{id}/cash-flows/      Cash flow schedule
GET    /bonds/{id}/key-rate-durations/
POST   /bonds/{id}/price/
POST   /bonds/{id}/ytm/
POST   /bonds/{id}/spread/
POST   /bonds/{id}/total-return/

GET    /portfolios/                 List portfolios
POST   /portfolios/{id}/positions/
GET    /portfolios/{id}/analytics/
POST   /portfolios/{id}/var/
POST   /portfolios/{id}/scenarios/
POST   /portfolios/{id}/custom-scenario/

GET    /curves/treasury/            Live UST curve (FRED)
GET    /curves/treasury/regime/
POST   /curves/                     Fit custom curve
POST   /curves/{id}/forecast/       ML rate forecast

GET    /analytics/benchmark-spreads/
POST   /analytics/quick-price/
POST   /analytics/duration-approximation/
POST   /analytics/rolling-volatility/
```

## Running with the Backend

```bash
# Terminal 1 — Backend
cd code/backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver

# Terminal 2 — Frontend
cd quantyield-frontend
npm install
npm run dev
```

The frontend dev server proxies nothing by default — update `vite.config.js` to add a proxy:

```js
server: {
  port: 3000,
  proxy: {
    '/api': 'http://localhost:8000',
  }
}
```

## Production Build

```bash
npm run build
# Output in dist/ — serve with any static host (Nginx, Vercel, Netlify, S3)
```

For Docker, add to the existing `docker-compose.yml`:

```yaml
frontend:
  image: node:20-alpine
  working_dir: /app
  volumes: [./quantyield-frontend:/app]
  command: sh -c "npm install && npm run build && npm run preview -- --host 0.0.0.0 --port 4173"
  ports: ["4173:4173"]
```
