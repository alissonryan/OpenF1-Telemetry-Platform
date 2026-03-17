# F1 Telemetry - Tech Stack

## Overview

Este documento define a stack tecnológica oficial do projeto F1 Telemetry Platform.

## Frontend Stack

### Core Framework
- **Next.js 14+** - App Router, Server Components, Streaming
- **React 18+** - Concurrent features, Suspense
- **TypeScript 5+** - Strict mode enabled

### Styling
- **Tailwind CSS 3.4+** - Utility-first CSS
- **Framer Motion 11+** - Production-ready animations
- **Radix UI** - Accessible component primitives

### Data Visualization
- **Recharts 2.12+** - React charts library
- **D3.js** (optional) - Custom visualizations
- **Three.js** (future) - 3D track visualization

### State & Data
- **TanStack Query v5** - Server state management
- **Zustand 4.5+** - Client state management
- **Socket.io Client 4.7+** - Real-time WebSocket

### Performance
- **React Virtual** - List virtualization
- **React Memo** - Component memoization
- **Dynamic Imports** - Code splitting

## Backend Stack

### Core Framework
- **FastAPI 0.109+** - Modern Python API framework
- **Uvicorn 0.27+** - ASGI server
- **Pydantic 2.6+** - Data validation

### Real-Time
- **WebSockets** - Native Python websockets
- **Socket.io** - Browser compatibility layer

### Data Processing
- **Fast-F1 3.4+** - F1 data library
- **Pandas 2.2+** - Data manipulation
- **NumPy 1.26+** - Numerical computing

### HTTP Client
- **HTTPX 0.26+** - Modern async HTTP client

## Machine Learning Stack

### Core ML
- **scikit-learn 1.4+** - Traditional ML algorithms
- **XGBoost 2.0+** - Gradient boosting
- **Joblib** - Model serialization

### Features
- **Feature-engine** - Feature engineering
- **SHAP** - Model explainability

### Training
- **Optuna** - Hyperparameter optimization
- **MLflow** (optional) - Experiment tracking

## Data Storage

### Application Data
- **PostgreSQL** (Supabase) - Primary database
- **Redis** (Upstash) - Caching & pub/sub

### ML Artifacts
- **Local filesystem** - Model storage
- **S3-compatible** (future) - Cloud storage

### Caching
- **Fast-F1 Cache** - Built-in telemetry cache
- **Redis** - Application cache
- **Browser Cache** - Static assets

## Infrastructure

### Development
- **Docker** - Containerization
- **Docker Compose** - Local orchestration

### Deployment
- **Vercel** - Frontend hosting
- **Railway/Fly.io** - Backend hosting
- **GitHub Actions** - CI/CD

### Monitoring
- **Sentry** - Error tracking
- **PostHog** - Analytics

## API Integration

### OpenF1 API
```yaml
baseUrl: https://api.openf1.org/v1
auth: none
rateLimit: 30 requests/minute
features:
  - car_data (3.7Hz)
  - position (4s interval)
  - laps
  - pit
  - stints
  - weather
  - team_radio
  - race_control
```

### Fast-F1
```yaml
type: python-library
installation: pip install fastf1
features:
  - telemetry extraction
  - lap analysis
  - session data
  - historical data (since 2018)
caching:
  enabled: true
  path: ./cache/fastf1
```

## Development Tools

### Code Quality
- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting
- **Ruff** - Python linting
- **Black** - Python formatting

### Testing
- **Vitest** - Unit tests (frontend)
- **Playwright** - E2E tests
- **Pytest** - Python tests

### Type Safety
- **TypeScript strict mode**
- **Pydantic models**
- **Zod schemas** (runtime validation)

## Version Requirements

```json
{
  "node": ">=20.0.0",
  "npm": ">=10.0.0",
  "python": ">=3.11.0",
  "pip": ">=24.0"
}
```

## Package Manager

- **pnpm** - Frontend (recommended)
- **uv** - Python (recommended)
