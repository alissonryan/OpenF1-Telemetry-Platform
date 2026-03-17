# F1 Telemetry Platform - Expansion Plan

## Overview

This document outlines the expansion plan for the F1 Telemetry Platform, integrating new data sources and features to create a comprehensive F1 analytics tool.

## Resources Identified

| Resource | Description | License | Priority |
|----------|-------------|---------|----------|
| [f1-circuits](https://github.com/bacinger/f1-circuits) | 39+ circuits in GeoJSON format | MIT | HIGH |
| [F1DB](https://github.com/f1db/f1db) | Complete F1 database (1950-present) | CC-BY-4.0 | HIGH |
| [Open-Meteo](https://open-meteo.com/) | Free weather API | CC-BY-4.0 | MEDIUM |
| [TracingInsights](https://github.com/TracingInsights) | F1 analytics reference | - | LOW |

---

## Phase 1: Enhanced Track Maps + Weather (Sprint 1-2)

### Goal
Complete track visualization with accurate circuits and real-time weather data.

### Features

#### 1.1 Circuit Integration (f1-circuits)
- **Priority**: Must Have
- **Effort**: 3 days
- **Dependencies**: None

**Tasks**:
- [ ] Download f1-circuits GeoJSON files
- [ ] Convert GeoJSON to normalized coordinates (0-1000)
- [ ] Update `trackData.ts` with 39 circuits
- [ ] Add circuit metadata (length, turns, sectors, DRS zones)
- [ ] Update TrackMap component to load dynamic circuits

**Files to create/modify**:
- `apps/web/src/lib/circuits/` - Circuit data files
- `apps/web/src/lib/trackData.ts` - Update with all circuits
- `apps/api/app/services/circuit_service.py` - Backend circuit service

**Acceptance Criteria**:
- All 39 circuits available in TrackMap
- Accurate track layouts matching real circuits
- Circuit metadata displayed (length, turns, country)

#### 1.2 Weather Integration (Open-Meteo)
- **Priority**: Should Have
- **Effort**: 2 days
- **Dependencies**: Circuit coordinates

**Tasks**:
- [ ] Create Open-Meteo API client
- [ ] Fetch weather by circuit coordinates
- [ ] Display current weather in dashboard
- [ ] Show weather forecast for race weekend
- [ ] Integrate weather into ML predictions

**Files to create/modify**:
- `apps/api/app/services/weather_service.py` - Open-Meteo client
- `apps/api/app/routers/weather.py` - Weather endpoints
- `apps/web/src/components/dashboard/WeatherWidget.tsx` - Weather display
- `apps/web/src/hooks/useWeather.ts` - Weather hook

**Weather Variables**:
- Temperature (air, track)
- Wind speed and direction
- Precipitation probability
- Humidity
- Pressure

**Acceptance Criteria**:
- Real-time weather for each circuit
- 7-day forecast for race weekends
- Weather impact on lap times

---

## Phase 2: Historical Data Integration (Sprint 3-4)

### Goal
Comprehensive historical data for analysis and ML training.

### Features

#### 2.1 F1DB Integration
- **Priority**: Must Have
- **Effort**: 5 days
- **Dependencies**: Database setup

**Tasks**:
- [ ] Download F1DB SQLite database
- [ ] Create F1DB service in backend
- [ ] Import circuit, driver, team data
- [ ] Create historical statistics endpoints
- [ ] Build statistics dashboard

**Files to create/modify**:
- `data/f1db/` - F1DB database files
- `apps/api/app/services/f1db_service.py` - F1DB client
- `apps/api/app/routers/statistics.py` - Stats endpoints
- `apps/web/src/app/statistics/` - Stats pages

**Data Available**:
- All drivers (1950-present)
- All constructors and engines
- All circuits with layouts
- Race results, qualifying, practice
- Lap times, pit stops
- Championship standings

**Acceptance Criteria**:
- Historical data accessible via API
- Statistics pages for drivers, teams, circuits
- Data export functionality

#### 2.2 Circuit SVG Assets
- **Priority**: Could Have
- **Effort**: 1 day
- **Dependencies**: F1DB

**Tasks**:
- [ ] Download circuit SVG files from F1DB
- [ ] Integrate into TrackMap component
- [ ] Add circuit selection by year/layout

---

## Phase 3: Fantasy F1 Helper (Sprint 5-6)

### Goal
AI-powered Fantasy F1 recommendations and predictions.

### Features

#### 3.1 Fantasy Points Predictor
- **Priority**: Must Have
- **Effort**: 4 days
- **Dependencies**: F1DB, ML models

**Tasks**:
- [ ] Create Fantasy F1 scoring model
- [ ] Train ML model on historical points
- [ ] Predict points per driver for next race
- [ ] Calculate expected value (points/cost)
- [ ] Build Fantasy recommendations page

**Files to create/modify**:
- `apps/api/app/ml/fantasy_predictor.py` - Fantasy ML model
- `apps/api/app/routers/fantasy.py` - Fantasy endpoints
- `apps/web/src/app/fantasy/` - Fantasy pages
- `apps/web/src/components/fantasy/` - Fantasy components

**Fantasy Variables**:
- Qualifying position
- Race finish position
- Overtakes made
- Fastest lap
- Driver of the day
- Constructor points

**Acceptance Criteria**:
- Point predictions for all drivers
- Cost/benefit analysis
- Recommended team composition
- Historical accuracy displayed

#### 3.2 Driver Recommendation Engine
- **Priority**: Should Have
- **Effort**: 3 days
- **Dependencies**: Fantasy predictor

**Tasks**:
- [ ] Create recommendation algorithm
- [ ] Consider budget constraints
- [ ] Optimize team composition
- [ ] Add driver comparison tool

**Recommendation Types**:
- Best value drivers
- Must-have drivers
- Risk/reward picks
- Budget team vs premium team

---

## Phase 4: Advanced Analytics (Sprint 7-8)

### Goal
Advanced telemetry analysis inspired by TracingInsights.

### Features

#### 4.1 Tyre Degradation Analysis
- **Priority**: Should Have
- **Effort**: 3 days

**Tasks**:
- [ ] Calculate tyre degradation curves
- [ ] Compare compounds performance
- [ ] Predict optimal pit windows
- [ ] Display degradation charts

#### 4.2 Driver Performance Metrics
- **Priority**: Could Have
- **Effort**: 2 days

**Tasks**:
- [ ] Calculate driver consistency
- [ ] Sector performance analysis
- [ ] Overtaking ability score
- [ ] Qualifying vs race pace

---

## Phase 5: Documentation & Community (Sprint 9-10)

### Goal
Launch-ready documentation and community resources.

### Features

#### 5.1 API Documentation
- **Priority**: Must Have
- **Effort**: 2 days

**Tasks**:
- [ ] Complete OpenAPI documentation
- [ ] Create API usage examples
- [ ] Add rate limiting documentation
- [ ] Create Postman collection

#### 5.2 Contribution Guide
- **Priority**: Must Have
- **Effort**: 1 day

**Tasks**:
- [ ] Create CONTRIBUTING.md
- [ ] Add code of conduct
- [ ] Document development setup
- [ ] Create issue templates

#### 5.3 Demo & Deployment
- **Priority**: Must Have
- **Effort**: 2 days

**Tasks**:
- [ ] Deploy frontend to Vercel
- [ ] Deploy backend to Railway
- [ ] Set up CI/CD pipeline
- [ ] Create demo video

---

## Dependencies Graph

```
Phase 1 (Sprint 1-2)
├── f1-circuits integration
│   └── TrackMap enhancement
└── Open-Meteo integration
    └── Weather display

Phase 2 (Sprint 3-4)
├── F1DB integration
│   ├── Historical data
│   └── Statistics dashboard
└── Circuit SVG assets

Phase 3 (Sprint 5-6)
├── Fantasy F1 Predictor
│   ├── ML model training
│   └── Points prediction
└── Recommendation Engine
    └── Team optimization

Phase 4 (Sprint 7-8)
├── Tyre degradation
└── Driver metrics

Phase 5 (Sprint 9-10)
├── Documentation
├── Deployment
└── Community
```

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API rate limits | Medium | Low | Implement caching, rate limiting |
| Data accuracy | High | Medium | Cross-reference with official sources |
| ML model accuracy | Medium | Medium | Train on more data, validate regularly |
| Performance issues | Medium | Low | Optimize queries, implement pagination |
| OpenF1 live access | High | Low | Have fallback to historical data |

---

## Success Metrics

### Technical Metrics
- [ ] API response time < 200ms (p95)
- [ ] Frontend Lighthouse score > 90
- [ ] Test coverage > 80%
- [ ] Zero critical security vulnerabilities

### User Metrics
- [ ] 39+ circuits available
- [ ] 74+ years of historical data
- [ ] Fantasy predictions with >70% accuracy
- [ ] Weather data for all circuits

### Community Metrics
- [ ] 100+ GitHub stars in first month
- [ ] 10+ contributors
- [ ] Active discussions
- [ ] Featured in F1 community

---

## Timeline

| Sprint | Duration | Focus | Status |
|--------|----------|-------|--------|
| 1-2 | 4 weeks | Track Maps + Weather | Pending |
| 3-4 | 4 weeks | Historical Data | Pending |
| 5-6 | 4 weeks | Fantasy F1 | Pending |
| 7-8 | 4 weeks | Advanced Analytics | Pending |
| 9-10 | 4 weeks | Documentation + Launch | Pending |

**Total**: 20 weeks (5 months)

---

## Next Steps

### Immediate Actions (This Week)
1. ✅ Repository created and pushed
2. [ ] Download f1-circuits GeoJSON
3. [ ] Create circuit conversion script
4. [ ] Update TrackMap with new circuits
5. [ ] Create Open-Meteo service

### Sprint 1 Kickoff
- Start with f1-circuits integration
- Set up Open-Meteo API client
- Create weather widget component

---

## Notes

- All external data sources have permissive licenses (MIT, CC-BY)
- Attribution will be provided in the application
- Consider contributing back to f1-circuits and F1DB projects
- Monitor OpenF1 API changes and rate limits
- Plan for future Ergast API deprecation (use F1DB as backup)

---

*Last updated: March 2026*
*Version: 1.0*
