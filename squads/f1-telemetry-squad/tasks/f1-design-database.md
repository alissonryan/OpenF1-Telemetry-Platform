# Task: Design Database

## Metadata
- **Agent**: @f1-data-engineer
- **Sprint**: 1-2
- **Priority**: HIGH
- **Estimate**: 4h

## Objective
Criar schema do database para armazenar dados de telemetria, sessões, voltas e predições.

## Prerequisites
- [ ] Projeto inicializado
- [ ] PostgreSQL ou Supabase configurado

## Inputs
- Database schema draft (do agente f1-data-engineer)
- Requisitos de dados

## Outputs
- [ ] Migration files
- [ ] Models Pydantic
- [ ] Índices otimizados
- [ ] Seeds para dados iniciais

## Database Schema

### Migrations

```sql
-- migrations/001_sessions.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_key INTEGER UNIQUE NOT NULL,
    year INTEGER NOT NULL,
    round_number INTEGER NOT NULL,
    session_type VARCHAR(10) NOT NULL, -- FP1, FP2, FP3, Q, R
    circuit_name VARCHAR(100),
    circuit_key INTEGER,
    event_name VARCHAR(200),
    date_start TIMESTAMPTZ,
    date_end TIMESTAMPTZ,
    total_laps INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_session UNIQUE (year, round_number, session_type)
);

CREATE INDEX idx_sessions_year ON sessions(year);
CREATE INDEX idx_sessions_date ON sessions(date_start);

-- migrations/002_drivers.sql
CREATE TABLE drivers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    driver_number INTEGER NOT NULL,
    code VARCHAR(3) NOT NULL,
    full_name VARCHAR(100),
    team_name VARCHAR(100),
    team_color VARCHAR(7),
    country VARCHAR(3),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_driver_code UNIQUE (code)
);

-- migrations/003_session_drivers.sql
CREATE TABLE session_drivers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    driver_id UUID REFERENCES drivers(id) ON DELETE CASCADE,
    position INTEGER,
    grid_position INTEGER,
    status VARCHAR(50),
    points DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_session_driver UNIQUE (session_id, driver_id)
);

CREATE INDEX idx_session_drivers_session ON session_drivers(session_id);

-- migrations/004_laps.sql
CREATE TABLE laps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    driver_number INTEGER NOT NULL,
    lap_number INTEGER NOT NULL,
    lap_time_seconds DECIMAL(10,3),
    sector_1_seconds DECIMAL(8,3),
    sector_2_seconds DECIMAL(8,3),
    sector_3_seconds DECIMAL(8,3),
    tire_compound VARCHAR(20),
    tire_age INTEGER,
    is_pit_in BOOLEAN DEFAULT FALSE,
    is_pit_out BOOLEAN DEFAULT FALSE,
    is_personal_best BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_session_driver_lap UNIQUE (session_id, driver_number, lap_number)
);

CREATE INDEX idx_laps_session ON laps(session_id);
CREATE INDEX idx_laps_driver ON laps(session_id, driver_number);
CREATE INDEX idx_lap_times ON laps(lap_time_seconds);

-- migrations/005_telemetry.sql
CREATE TABLE telemetry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    driver_number INTEGER NOT NULL,
    timestamp_ms BIGINT NOT NULL,
    speed DECIMAL(6,1),
    throttle DECIMAL(5,2),
    brake DECIMAL(5,2),
    drs INTEGER,
    gear INTEGER,
    rpm INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_telemetry_session_driver ON telemetry(session_id, driver_number);
CREATE INDEX idx_telemetry_timestamp ON telemetry(timestamp_ms);
-- Partitioning hint for large datasets:
-- CREATE INDEX idx_telemetry_partition ON telemetry (session_id, timestamp_ms);

-- migrations/006_positions.sql
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    driver_number INTEGER NOT NULL,
    timestamp_ms BIGINT NOT NULL,
    position INTEGER,
    x DECIMAL(10,2),
    y DECIMAL(10,2),
    z DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_positions_session_time ON positions(session_id, timestamp_ms);

-- migrations/007_pit_stops.sql
CREATE TABLE pit_stops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    driver_number INTEGER NOT NULL,
    lap_number INTEGER NOT NULL,
    pit_duration_seconds DECIMAL(6,3),
    tire_compound_old VARCHAR(20),
    tire_compound_new VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_session_driver_pit UNIQUE (session_id, driver_number, lap_number)
);

-- migrations/008_weather.sql
CREATE TABLE weather (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    timestamp_ms BIGINT NOT NULL,
    air_temp DECIMAL(5,2),
    track_temp DECIMAL(5,2),
    humidity DECIMAL(5,2),
    pressure DECIMAL(7,2),
    wind_speed DECIMAL(5,2),
    wind_direction INTEGER,
    rainfall BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_weather_session_time ON weather(session_id, timestamp_ms);

-- migrations/009_predictions.sql
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    driver_number INTEGER NOT NULL,
    prediction_type VARCHAR(50) NOT NULL, -- 'pit_stop', 'final_position'
    prediction_value DECIMAL(10,4),
    confidence DECIMAL(5,4),
    features JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_predictions_session ON predictions(session_id);
CREATE INDEX idx_predictions_type ON predictions(prediction_type);

-- migrations/010_ml_features.sql
CREATE TABLE ml_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    driver_number INTEGER NOT NULL,
    lap_number INTEGER NOT NULL,
    tire_age INTEGER,
    current_position INTEGER,
    gap_to_leader DECIMAL(10,3),
    gap_to_ahead DECIMAL(10,3),
    avg_lap_time DECIMAL(10,3),
    tire_degradation_rate DECIMAL(8,4),
    stops_completed INTEGER DEFAULT 0,
    weather_condition VARCHAR(20),
    safety_car_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_ml_feature UNIQUE (session_id, driver_number, lap_number)
);

CREATE INDEX idx_ml_features_session ON ml_features(session_id);
```

### Pydantic Models
```python
# app/models/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID

class SessionBase(BaseModel):
    year: int
    round_number: int
    session_type: str
    circuit_name: Optional[str] = None
    event_name: Optional[str] = None

class Session(SessionBase):
    id: UUID
    session_key: int
    date_start: Optional[datetime]
    total_laps: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

class LapBase(BaseModel):
    driver_number: int
    lap_number: int
    lap_time_seconds: Optional[float]
    sector_1_seconds: Optional[float]
    sector_2_seconds: Optional[float]
    sector_3_seconds: Optional[float]
    tire_compound: Optional[str]
    tire_age: Optional[int]

class Lap(LapBase):
    id: UUID
    session_id: UUID
    is_pit_in: bool
    is_pit_out: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TelemetryBase(BaseModel):
    driver_number: int
    timestamp_ms: int
    speed: Optional[float]
    throttle: Optional[float]
    brake: Optional[float]
    drs: Optional[int]
    gear: Optional[int]
    rpm: Optional[int]

class Telemetry(TelemetryBase):
    id: UUID
    session_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class PredictionBase(BaseModel):
    driver_number: int
    prediction_type: str
    prediction_value: float
    confidence: float

class Prediction(PredictionBase):
    id: UUID
    session_id: UUID
    features: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True
```

## Acceptance Criteria
- [ ] Todas as migrations executam sem erro
- [ ] Índices criados corretamente
- [ ] Foreign keys funcionando
- [ ] Pydantic models validam dados
- [ ] Seed data carregada

## Dependencies
- f1-setup-project

## Risks
- Volume de dados de telemetria pode crescer rapidamente
- Considerar particionamento para tabelas grandes
