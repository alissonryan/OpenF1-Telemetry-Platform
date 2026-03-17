# 🏎️ F1 Telemetry Platform - Quick Start

## Prerequisites

- Node.js >= 20.0.0
- Python >= 3.11
- npm >= 10.0.0

## 🚀 Quick Start (5 minutes)

### 1. Clone and Install

```bash
cd /Users/alissonryan/code/projeto-f1

# Install frontend dependencies
npm install

# Setup Python environment
cd apps/api
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start the Backend

```bash
# In apps/api directory with venv activated
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Backend will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. Start the Frontend

```bash
# In a new terminal
cd apps/web
npm run dev
```

Frontend will be available at: http://localhost:3000

### 4. Test the API

```bash
# In another terminal with venv activated
cd apps/api
source .venv/bin/activate
python test_endpoints.py
```

## 📊 Features

### ✅ Implemented

- **Backend API (FastAPI)**
  - OpenF1 API integration (11 endpoints)
  - Fast-F1 integration (historical data)
  - Rate limiting and retry logic
  - Comprehensive error handling
  - WebSocket support for real-time data

- **Frontend (Next.js 14)**
  - Dashboard page with telemetry charts
  - Session selector component
  - Driver cards with team colors
  - Telemetry charts (Speed, Throttle, Brake, RPM)
  - Leaderboard component
  - Zustand state management
  - Custom hooks for API calls
  - Framer Motion animations

### 🚧 In Progress

- ML predictions (pit stop, position forecast)
- Track map visualization
- Mobile optimization
- WebSocket real-time updates

## 🎨 Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, React 18, TypeScript |
| Styling | Tailwind CSS, Framer Motion |
| Charts | Recharts |
| Backend | FastAPI, WebSocket |
| ML | Fast-F1, scikit-learn, XGBoost |
| APIs | OpenF1 (real-time), Fast-F1 (historical) |

## 📁 Project Structure

```
projeto-f1/
├── apps/
│   ├── web/                    # Next.js Frontend
│   │   ├── src/
│   │   │   ├── app/            # App Router pages
│   │   │   │   ├── page.tsx           # Home page
│   │   │   │   └── dashboard/         # Dashboard page
│   │   │   ├── components/     # React components
│   │   │   │   ├── charts/            # TelemetryChart
│   │   │   │   ├── dashboard/         # DriverCard, SessionSelector, Leaderboard
│   │   │   │   └── layout/            # Layout, Header, Sidebar
│   │   │   ├── hooks/          # Custom hooks
│   │   │   │   └── useF1Data.ts       # F1 API hooks
│   │   │   └── stores/         # Zustand stores
│   │   │       └── f1Store.ts         # Global state
│   │   └── ...
│   │
│   └── api/                    # FastAPI Backend
│       ├── app/
│       │   ├── routers/        # API endpoints
│       │   │   ├── telemetry.py       # Car data, positions, laps
│       │   │   ├── sessions.py        # Meetings, sessions
│       │   │   ├── fastf1.py          # Historical data
│       │   │   └── predictions.py     # ML predictions
│       │   ├── services/       # Business logic
│       │   │   ├── openf1_client.py   # OpenF1 API client
│       │   │   └── fastf1_service.py  # Fast-F1 integration
│       │   ├── models/         # Pydantic models
│       │   └── ml/             # ML models
│       ├── tests/              # Test scripts
│       └── test_endpoints.py   # Quick validation
│
├── packages/shared/            # Shared types
├── data/cache/                 # Fast-F1 cache
└── squads/                     # Squad configuration
```

## 🔌 API Endpoints

### Telemetry
- `GET /api/telemetry/car-data` - Real-time car data
- `GET /api/telemetry/positions` - Driver positions
- `GET /api/telemetry/laps` - Lap timing data
- `GET /api/telemetry/drivers` - Driver information
- `GET /api/telemetry/intervals` - Time gaps

### Sessions
- `GET /api/sessions/meetings` - F1 meetings
- `GET /api/sessions/sessions` - Session information
- `GET /api/sessions/weather` - Weather data
- `GET /api/sessions/pit` - Pit stop data
- `GET /api/sessions/stints` - Tyre stints

### Fast-F1 (Historical)
- `POST /api/fastf1/load-session` - Load historical session
- `GET /api/fastf1/telemetry` - Get telemetry data
- `GET /api/fastf1/laps` - Get lap data
- `GET /api/fastf1/weather` - Get weather data
- `GET /api/fastf1/tyre-analysis` - Tyre degradation analysis

### Predictions
- `POST /api/predictions/pit-stop` - Predict pit stop timing
- `GET /api/predictions/position-forecast` - Forecast positions

### WebSocket
- `WS /ws` - Real-time data streaming

## 🎯 Next Steps

1. **Start the backend** (see above)
2. **Start the frontend** (see above)
3. **Open** http://localhost:3000/dashboard
4. **Select a session** (meeting + session type)
5. **Select drivers** to view telemetry
6. **Watch real-time data** update every second!

## 🐛 Troubleshooting

### Backend won't start
```bash
# Make sure venv is activated
cd apps/api
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend won't start
```bash
# Install dependencies
cd apps/web
npm install
```

### API returns 404
```bash
# Check if backend is running
curl http://localhost:8000/health

# Test endpoints
cd apps/api
python test_endpoints.py
```

## 📝 Development

```bash
# Run all services with Turbo
npm run dev

# Run linting
npm run lint

# Run type checking
npm run typecheck

# Format code
npm run format
```

## 🚢 Deployment

### Frontend (Vercel)
```bash
cd apps/web
vercel
```

### Backend (Railway/Render)
```bash
# Build Docker image
docker build -t f1-telemetry-api ./apps/api

# Deploy
railway up
```

---

Built with 🏎️ by the F1 Telemetry Squad
