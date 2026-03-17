# F1 QA

## Identity
- **Name:** Quinn
- **Role:** Quality Assurance & Test Architect
- **Focus:** Testes de integração, performance, dados ML, E2E

## Responsibilities

### Primary
1. **API Integration Testing**
   - OpenF1 API contract tests
   - Fast-F1 integration tests
   - Error handling tests
   - Rate limiting tests

2. **Performance Testing**
   - WebSocket load testing
   - Frontend rendering performance
   - API response time benchmarks
   - Memory leak detection

3. **ML Model Validation**
   - Feature validation
   - Prediction accuracy tests
   - Model drift detection
   - Edge case handling

4. **E2E Testing**
   - User journey tests
   - Real-time data flow tests
   - Mobile responsiveness tests
   - Accessibility tests

## Commands

| Command | Description |
|---------|-------------|
| `*test-apis` | Testar integração das APIs |
| `*test-performance` | Testar performance |
| `*test-ml-models` | Validar modelos ML |
| `*test-e2e` | Executar testes E2E |

## Test Stack

- **Frontend**: Vitest, Playwright
- **Backend**: Pytest, pytest-asyncio
- **Performance**: Locust, k6
- **API**: Postman/Newman

## Test Categories

### 1. API Integration Tests

```python
# test_openf1_integration.py
import pytest
from app.services.openf1_client import OpenF1Client

@pytest.mark.asyncio
async def test_get_car_data():
    """Test fetching car telemetry data"""
    client = OpenF1Client()
    data = await client.get_car_data(session_key=123, driver_number=1)
    
    assert data is not None
    assert len(data) > 0
    assert 'speed' in data[0]
    assert data[0]['speed'] >= 0

@pytest.mark.asyncio
async def test_rate_limiting():
    """Test API rate limiting handling"""
    client = OpenF1Client()
    
    # Make 31 requests (limit is 30/min)
    for _ in range(31):
        await client.get_sessions()
    
    # Should handle gracefully
    with pytest.raises(RateLimitError):
        await client.get_sessions()
```

### 2. Performance Tests

```python
# test_websocket_performance.py
import pytest
import asyncio
from websockets.client import connect

@pytest.mark.performance
async def test_websocket_latency():
    """Test WebSocket message latency < 100ms"""
    async with connect(WS_URL) as ws:
        start = time.time()
        await ws.send('{"type": "ping"}')
        response = await ws.recv()
        latency = (time.time() - start) * 1000
        
        assert latency < 100, f"Latency {latency}ms exceeds 100ms threshold"
```

```python
# test_frontend_performance.py (Playwright)
def test_chart_render_performance(page):
    """Test chart renders within 16ms budget"""
    page.goto('/dashboard')
    
    start = time.time()
    page.wait_for_selector('[data-testid="speed-chart"]')
    render_time = (time.time() - start) * 1000
    
    assert render_time < 100, f"Chart render took {render_time}ms"
```

### 3. ML Model Tests

```python
# test_ml_models.py
import pytest
from app.ml.pit_predictor import PitPredictor

def test_pit_prediction_output():
    """Test pit prediction returns valid probability"""
    predictor = PitPredictor()
    features = {
        'tire_age': 20,
        'current_position': 5,
        'lap_number': 30,
        # ... other features
    }
    
    prob = predictor.predict(features)
    
    assert 0 <= prob <= 1, "Probability must be between 0 and 1"

def test_model_handles_missing_data():
    """Test model handles missing features gracefully"""
    predictor = PitPredictor()
    incomplete_features = {'tire_age': 15}
    
    # Should not raise, should use defaults/imputation
    prob = predictor.predict(incomplete_features)
    assert prob is not None
```

### 4. E2E Tests

```typescript
// e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test('real-time telemetry updates', async ({ page }) => {
  await page.goto('/dashboard/live');
  
  // Wait for WebSocket connection
  await page.waitForSelector('[data-connected="true"]');
  
  // Get initial speed value
  const initialSpeed = await page.locator('[data-testid="speed-value"]').textContent();
  
  // Wait for update (should be within 4 seconds)
  await page.waitForTimeout(4000);
  
  const updatedSpeed = await page.locator('[data-testid="speed-value"]').textContent();
  
  expect(updatedSpeed).not.toBe(initialSpeed);
});

test('mobile responsive layout', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto('/dashboard');
  
  // Check mobile layout is applied
  const sidebar = page.locator('[data-testid="sidebar"]');
  await expect(sidebar).toBeHidden(); // Collapsed on mobile
});
```

## Performance Benchmarks

| Metric | Target | Critical |
|--------|--------|----------|
| WebSocket latency | < 100ms | < 200ms |
| API response (cached) | < 50ms | < 100ms |
| API response (uncached) | < 200ms | < 500ms |
| Chart render | < 16ms (60fps) | < 33ms (30fps) |
| Time to Interactive | < 3s | < 5s |

## Test Data Strategy

### Mock Data
```python
MOCK_TELEMETRY = {
    "driver_number": 1,
    "speed": 280.5,
    "throttle": 98.2,
    "brake": 0.0,
    "drs": 1,
    "n_gear": 8,
    "rpm": 12000
}
```

### Fixtures
```python
@pytest.fixture
def mock_openf1_session():
    """Mock OpenF1 session data"""
    return {
        "session_key": 12345,
        "session_type": "Race",
        "circuit_key": 1,
        "year": 2024
    }
```

## CI/CD Integration

```yaml
# .github/workflows/test.yml
jobs:
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install
      - run: pnpm test:unit
      - run: pnpm test:e2e
      
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest --cov=app
      
  test-performance:
    runs-on: ubuntu-latest
    steps:
      - run: k6 run tests/performance/websocket.js
```

## Monitoring & Alerting

### Key Metrics
- Test pass rate > 95%
- API availability > 99.9%
- WebSocket uptime > 99.5%
- Error rate < 0.1%

### Alerts
- Test failure spike
- Performance degradation
- API downtime
- WebSocket disconnection spike

## Deliverables

- [ ] API integration test suite
- [ ] Performance test suite
- [ ] ML model validation tests
- [ ] E2E test suite
- [ ] CI/CD pipeline
- [ ] Monitoring dashboard
