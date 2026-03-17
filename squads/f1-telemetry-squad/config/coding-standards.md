# F1 Telemetry - Coding Standards

## General Principles

1. **Performance First** - Real-time data requires optimized code
2. **Type Safety** - Strict typing everywhere
3. **Test Coverage** - Critical paths must be tested
4. **Documentation** - Complex algorithms need docs

## TypeScript/JavaScript

### File Naming
```
components/Button.tsx        # PascalCase for components
hooks/useWebSocket.ts        # camelCase for utilities
lib/api-client.ts            # kebab-case for files
types/telemetry.d.ts         # .d.ts for type definitions
```

### Component Structure
```tsx
// 1. Imports (sorted: external, internal, types)
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import type { TelemetryData } from '@/types';

// 2. Types
interface Props {
  driverId: string;
  onDataUpdate?: (data: TelemetryData) => void;
}

// 3. Component
export function TelemetryChart({ driverId, onDataUpdate }: Props) {
  // Hooks at the top
  const { data, isLoading } = useQuery({...});
  
  // Memoized values
  const chartData = useMemo(() => transformData(data), [data]);
  
  // Effects
  useEffect(() => {...}, [deps]);
  
  // Handlers
  const handleClick = useCallback(() => {...}, [deps]);
  
  // Early returns
  if (isLoading) return <Skeleton />;
  
  // Render
  return (
    <motion.div {...animations}>
      {/* ... */}
    </motion.div>
  );
}
```

### Performance Patterns
```tsx
// ✅ Memoize expensive computations
const processedData = useMemo(
  () => heavyTransform(rawData),
  [rawData]
);

// ✅ Memoize callbacks
const handleUpdate = useCallback(
  (data: Telemetry) => updateStore(data),
  [updateStore]
);

// ✅ Virtualize long lists
import { useVirtualizer } from '@tanstack/react-virtual';

// ✅ Debounce rapid updates
const debouncedValue = useDebouncedValue(value, 100);
```

### Real-Time Data Handling
```tsx
// ✅ Use WebSocket with reconnection
const { status, data, send } = useWebSocket(WS_URL, {
  reconnectAttempts: 5,
  reconnectInterval: 1000,
});

// ✅ Buffer rapid updates
const bufferedData = useDataBuffer(data, {
  maxBufferSize: 100,
  flushInterval: 100,
});

// ✅ Animate with requestAnimationFrame
useAnimationFrame((deltaTime) => {
  updatePosition(deltaTime);
});
```

## Python

### File Naming
```
routers/telemetry.py         # snake_case for modules
services/data_service.py     # snake_case for services
models/schemas.py            # snake_case for schemas
```

### Code Structure
```python
# 1. Standard library imports
from typing import Optional, List

# 2. Third-party imports
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# 3. Local imports
from app.services.telemetry import TelemetryService

# 4. Constants
MAX_BUFFER_SIZE = 1000
UPDATE_INTERVAL = 0.25  # seconds

# 5. Models
class TelemetryResponse(BaseModel):
    driver_id: str
    speed: float
    throttle: float
    brake: float

# 6. Router/Service
router = APIRouter()

@router.get("/telemetry/{driver_id}")
async def get_telemetry(driver_id: str) -> TelemetryResponse:
    """Fetch real-time telemetry for a driver."""
    # Implementation
    pass
```

### Fast-F1 Patterns
```python
# ✅ Use caching
import fastf1
fastf1.Cache.enable_cache('./cache/fastf1')

# ✅ Session loading with error handling
async def load_session(year: int, round: int, session_type: str):
    try:
        session = fastf1.get_session(year, round, session_type)
        await session.load()
        return session
    except Exception as e:
        logger.error(f"Failed to load session: {e}")
        raise HTTPException(500, "Session data unavailable")

# ✅ Efficient data extraction
def get_telemetry_dataframe(session, driver: str):
    lap = session.laps.pick_driver(driver).pick_fastest()
    return lap.get_car_data().add_distance()
```

### ML Model Patterns
```python
# ✅ Use Pydantic for input validation
class PredictionInput(BaseModel):
    driver_id: str
    current_lap: int
    tire_age: int
    position: int
    gap_to_leader: float

# ✅ Separate training from inference
class PitStopPredictor:
    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)
    
    def predict(self, features: PredictionInput) -> float:
        """Return probability of pit stop in next 5 laps."""
        X = self._preprocess(features)
        return self.model.predict_proba(X)[0][1]
```

## Git Conventions

### Branch Names
```
feature/f1-dashboard-core
fix/websocket-reconnection
refactor/telemetry-service
docs/api-documentation
```

### Commit Messages
```
feat(dashboard): add real-time telemetry chart
fix(ws): handle connection timeout gracefully
perf(ml): optimize prediction inference time
docs(readme): update installation instructions
```

## Testing Standards

### Frontend Tests
```tsx
// Component test
describe('TelemetryChart', () => {
  it('should render loading state', () => {
    render(<TelemetryChart driverId="VER" />);
    expect(screen.getByTestId('skeleton')).toBeInTheDocument();
  });
  
  it('should update on new data', async () => {
    const { rerender } = render(<TelemetryChart data={mockData} />);
    rerender(<TelemetryChart data={updatedData} />);
    await waitFor(() => {
      expect(screen.getByText('280 km/h')).toBeInTheDocument();
    });
  });
});
```

### Backend Tests
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_telemetry(client: AsyncClient):
    response = await client.get("/api/telemetry/VER")
    assert response.status_code == 200
    data = response.json()
    assert "speed" in data
    assert data["speed"] >= 0
```

## Error Handling

### Frontend
```tsx
// ✅ Error boundaries
<ErrorBoundary fallback={<ErrorFallback />}>
  <TelemetryDashboard />
</ErrorBoundary>

// ✅ Graceful degradation
const { data, error, isError } = useQuery({
  queryKey: ['telemetry'],
  queryFn: fetchTelemetry,
  retry: 3,
  onError: (err) => toast.error('Connection lost'),
});
```

### Backend
```python
from fastapi import HTTPException

# ✅ Proper HTTP exceptions
@router.get("/telemetry/{driver_id}")
async def get_telemetry(driver_id: str):
    try:
        data = await fetch_telemetry(driver_id)
        if not data:
            raise HTTPException(404, "Driver not found")
        return data
    except ConnectionError:
        raise HTTPException(503, "Live data unavailable")
```

## Performance Budgets

| Metric | Budget | Action |
|--------|--------|--------|
| First Contentful Paint | < 1.5s | Optimize critical path |
| Time to Interactive | < 3s | Code splitting |
| WebSocket latency | < 100ms | Edge deployment |
| Chart render time | < 16ms | WebWorker for calculations |
| API response time | < 200ms | Caching, pagination |
