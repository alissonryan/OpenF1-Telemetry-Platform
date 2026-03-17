# F1 Telemetry Platform

Real-time F1 telemetry dashboard and ML-powered predictions for Formula 1.

## 🏎️ Features

- **Live Telemetry**: Real-time car data including speed, throttle, brake, and gear at 3.7Hz
- **Track Position**: Live driver positions on track with timing data
- **ML Predictions**: AI-powered pit stop and position predictions
- **Strategy Analysis**: Tyre strategy and pit window recommendations

## 🛠️ Tech Stack

### Frontend
- **Next.js 14** - App Router, Server Components
- **React 18** - Concurrent features
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Recharts** - Data visualization
- **Framer Motion** - Animations

### Backend
- **FastAPI** - Modern Python API framework
- **Fast-F1** - F1 data library
- **scikit-learn** - Machine learning
- **WebSockets** - Real-time communication

### Data Sources
- **OpenF1 API** - Real-time telemetry data
- **Fast-F1** - Historical data and advanced analysis

## 📁 Project Structure

```
projeto-f1/
├── apps/
│   ├── web/                    # Next.js Frontend
│   │   ├── src/
│   │   │   ├── app/            # App Router pages
│   │   │   ├── components/     # React components
│   │   │   ├── hooks/          # Custom hooks
│   │   │   ├── stores/         # Zustand stores
│   │   │   ├── lib/            # Utilities
│   │   │   └── types/          # TypeScript types
│   │   └── ...
│   │
│   └── api/                    # FastAPI Backend
│       ├── app/
│       │   ├── routers/        # API endpoints
│       │   ├── services/       # Business logic
│       │   ├── models/         # Pydantic models
│       │   ├── ml/             # Machine learning
│       │   └── core/           # Configuration
│       └── ...
│
├── packages/
│   └── shared/                 # Shared types & utilities
│
├── data/
│   └── cache/                  # Fast-F1 cache
│
└── squads/
    └── f1-telemetry-squad/     # Squad configuration
```

## 🚀 Getting Started

### Prerequisites

- **Node.js** >= 20.0.0
- **Python** >= 3.11
- **npm** >= 10.0.0

### Installation

1. **Clone the repository**
   ```bash
   cd projeto-f1
   ```

2. **Install frontend dependencies**
   ```bash
   npm install
   cd apps/web && npm install
   ```

3. **Setup Python environment**
   ```bash
   cd apps/api
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

### Development

**Run frontend:**
```bash
npm run dev:web
# or
cd apps/web && npm run dev
```
Frontend will be available at http://localhost:3000

**Run backend:**
```bash
npm run dev:api
# or
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload
```
Backend will be available at http://localhost:8000

**Run with Docker:**
```bash
docker-compose up
```

### Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start all services (Turbo) |
| `npm run dev:web` | Start frontend only |
| `npm run dev:api` | Start backend only |
| `npm run build` | Build all packages |
| `npm run lint` | Lint all code |
| `npm run format` | Format code with Prettier |
| `npm run typecheck` | Type check TypeScript |

## 📊 API Documentation

Once the backend is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/telemetry/car-data` | Get real-time car telemetry |
| `GET /api/telemetry/position` | Get driver positions |
| `GET /api/telemetry/laps` | Get lap timing data |
| `GET /api/sessions/meetings` | Get F1 meetings |
| `GET /api/sessions/` | Get session information |
| `POST /api/predictions/pit-stop` | Predict pit stop timing |
| `GET /api/predictions/position-forecast` | Forecast positions |
| `WS /ws/` | WebSocket for real-time data |

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# OpenF1 API
OPENF1_BASE_URL=https://api.openf1.org/v1

# Fast-F1
FASTF1_CACHE_DIR=./data/cache/fastf1

# ML Models
MODELS_DIR=./packages/ml-models
```

## 🧪 Testing

```bash
# Frontend tests
cd apps/web && npm test

# Backend tests
cd apps/api
source .venv/bin/activate
pytest
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

# Deploy to Railway
railway up
```

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

## 🤝 Contributing

This project uses the F1 Telemetry Squad workflow. See `squads/f1-telemetry-squad/` for more details.

---

Built with 🏎️ by the F1 Telemetry Squad
