# F1 Telemetry - Source Tree

## Project Structure

```
projeto-f1/
│
├── apps/
│   ├── web/                          # Next.js Frontend Application
│   │   ├── src/
│   │   │   ├── app/                  # App Router pages
│   │   │   │   ├── layout.tsx        # Root layout
│   │   │   │   ├── page.tsx          # Home page
│   │   │   │   ├── dashboard/        # Real-time dashboard
│   │   │   │   │   ├── page.tsx
│   │   │   │   │   └── [session]/    # Dynamic session routes
│   │   │   │   ├── predictions/      # ML predictions page
│   │   │   │   │   └── page.tsx
│   │   │   │   └── api/              # API routes (if needed)
│   │   │   │
│   │   │   ├── components/
│   │   │   │   ├── ui/               # Base UI components
│   │   │   │   │   ├── button.tsx
│   │   │   │   │   ├── card.tsx
│   │   │   │   │   └── skeleton.tsx
│   │   │   │   ├── charts/           # Chart components
│   │   │   │   │   ├── speed-chart.tsx
│   │   │   │   │   ├── telemetry-chart.tsx
│   │   │   │   │   ├── track-map.tsx
│   │   │   │   │   └── position-chart.tsx
│   │   │   │   ├── dashboard/        # Dashboard components
│   │   │   │   │   ├── driver-card.tsx
│   │   │   │   │   ├── live-feed.tsx
│   │   │   │   │   ├── weather-widget.tsx
│   │   │   │   │   └── timing-board.tsx
│   │   │   │   ├── predictions/      # ML prediction components
│   │   │   │   │   ├── pit-predictor.tsx
│   │   │   │   │   ├── position-forecast.tsx
│   │   │   │   │   └── strategy-analyzer.tsx
│   │   │   │   └── layout/           # Layout components
│   │   │   │       ├── header.tsx
│   │   │   │       ├── sidebar.tsx
│   │   │   │       └── footer.tsx
│   │   │   │
│   │   │   ├── hooks/                # Custom React hooks
│   │   │   │   ├── use-telemetry.ts  # Telemetry data hook
│   │   │   │   ├── use-websocket.ts  # WebSocket connection
│   │   │   │   ├── use-predictions.ts # ML predictions hook
│   │   │   │   └── use-session.ts    # Session data hook
│   │   │   │
│   │   │   ├── stores/               # Zustand stores
│   │   │   │   ├── telemetry-store.ts
│   │   │   │   ├── session-store.ts
│   │   │   │   └── ui-store.ts
│   │   │   │
│   │   │   ├── lib/                  # Utility libraries
│   │   │   │   ├── api-client.ts     # API client
│   │   │   │   ├── websocket.ts      # WebSocket client
│   │   │   │   ├── formatters.ts     # Data formatters
│   │   │   │   └── constants.ts      # App constants
│   │   │   │
│   │   │   └── types/                # TypeScript types
│   │   │       ├── telemetry.d.ts
│   │   │       ├── session.d.ts
│   │   │       └── predictions.d.ts
│   │   │
│   │   ├── public/
│   │   │   ├── images/               # Static images
│   │   │   └── fonts/                 # Custom fonts
│   │   │
│   │   ├── next.config.js
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   └── api/                          # FastAPI Backend Application
│       ├── app/
│       │   ├── main.py               # FastAPI app entry
│       │   ├── routers/              # API routers
│       │   │   ├── __init__.py
│       │   │   ├── telemetry.py      # Telemetry endpoints
│       │   │   ├── sessions.py       # Session endpoints
│       │   │   ├── predictions.py    # ML prediction endpoints
│       │   │   └── websocket.py      # WebSocket router
│       │   │
│       │   ├── services/             # Business logic
│       │   │   ├── __init__.py
│       │   │   ├── openf1_client.py  # OpenF1 API client
│       │   │   ├── fastf1_service.py # Fast-F1 integration
│       │   │   ├── telemetry_service.py
│       │   │   └── prediction_service.py
│       │   │
│       │   ├── models/               # Pydantic models
│       │   │   ├── __init__.py
│       │   │   ├── telemetry.py
│       │   │   ├── session.py
│       │   │   └── predictions.py
│       │   │
│       │   ├── ml/                   # Machine Learning
│       │   │   ├── __init__.py
│       │   │   ├── pit_predictor.py
│       │   │   ├── position_forecast.py
│       │   │   ├── feature_engineer.py
│       │   │   └── trainer.py
│       │   │
│       │   ├── core/                 # Core configuration
│       │   │   ├── __init__.py
│       │   │   ├── config.py         # Settings
│       │   │   ├── logging.py        # Logging config
│       │   │   └── dependencies.py   # FastAPI deps
│       │   │
│       │   └── utils/                # Utilities
│       │       ├── __init__.py
│       │       ├── cache.py
│       │       └── helpers.py
│       │
│       ├── tests/                    # Test files
│       │   ├── __init__.py
│       │   ├── test_telemetry.py
│       │   ├── test_predictions.py
│       │   └── conftest.py
│       │
│       ├── pyproject.toml
│       ├── requirements.txt
│       └── Dockerfile
│
├── packages/
│   ├── shared/                       # Shared types & utilities
│   │   ├── src/
│   │   │   ├── types/
│   │   │   │   ├── telemetry.ts
│   │   │   │   └── predictions.ts
│   │   │   └── utils/
│   │   │       ├── formatters.ts
│   │   │       └── constants.ts
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── ml-models/                    # Trained ML models
│       ├── pit_predictor_v1.pkl
│       ├── position_forecast_v1.pkl
│       └── metadata.json
│
├── data/
│   ├── cache/                        # Fast-F1 cache
│   │   └── fastf1/
│   ├── raw/                          # Raw downloaded data
│   └── processed/                    # Processed datasets
│
├── squads/
│   └── f1-telemetry-squad/           # This squad
│       ├── squad.yaml
│       ├── README.md
│       ├── config/
│       ├── agents/
│       ├── tasks/
│       └── ...
│
├── docs/                             # Project documentation
│   ├── prd/                          # Product requirements
│   ├── architecture/                 # Architecture docs
│   └── api/                          # API documentation
│
├── docker-compose.yml                # Local development
├── Dockerfile                        # Production build
├── .env.example                      # Environment template
├── package.json                      # Root package.json
├── pnpm-workspace.yaml               # pnpm workspaces
└── turbo.json                        # Turborepo config
```

## Key Directories Explained

### `/apps/web/src/components/`
All React components organized by domain:
- `ui/` - Generic, reusable components
- `charts/` - Data visualization components
- `dashboard/` - Dashboard-specific components
- `predictions/` - ML prediction UI
- `layout/` - Layout and navigation

### `/apps/api/app/routers/`
FastAPI routers for each domain:
- `telemetry.py` - Real-time telemetry data
- `sessions.py` - Session management
- `predictions.py` - ML prediction endpoints
- `websocket.py` - WebSocket handlers

### `/apps/api/app/ml/`
Machine learning module:
- `pit_predictor.py` - Pit stop prediction model
- `position_forecast.py` - Position forecasting
- `feature_engineer.py` - Feature extraction
- `trainer.py` - Model training pipeline

### `/packages/shared/`
Code shared between frontend and backend:
- TypeScript types (used for API contracts)
- Utility functions
- Constants

## Import Patterns

### Frontend
```tsx
// Absolute imports from src/
import { Button } from '@/components/ui/button';
import { useTelemetry } from '@/hooks/use-telemetry';
import type { TelemetryData } from '@/types/telemetry';
```

### Backend
```python
# Relative imports within app
from app.services.telemetry_service import TelemetryService
from app.models.telemetry import TelemetryResponse
from app.core.config import settings
```
