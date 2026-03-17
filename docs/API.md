# F1 Telemetry Platform - API Documentation

## Índice

- [Visão Geral](#visão-geral)
- [Autenticação](#autenticação)
- [Rate Limits](#rate-limits)
- [Endpoints](#endpoints)
  - [Telemetry](#telemetry)
  - [Sessions](#sessions)
  - [Fast-F1](#fast-f1)
  - [Predictions](#predictions)
  - [Weather](#weather)
  - [F1DB](#f1db)
  - [Fantasy](#fantasy)
- [WebSocket](#websocket)
- [Erros](#erros)
- [Exemplos](#exemplos)

---

## Visão Geral

### Base URL

```
http://localhost:8000
```

### Formatos

- **Request**: JSON
- **Response**: JSON
- **Codificação**: UTF-8

### Documentação Interativa

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Autenticação

Atualmente, a API é **aberta** e não requer autenticação para a maioria dos endpoints.

### Endpoints que requerem autenticação:
- Nenhum (por enquanto)

### Futuro:
- API keys para rate limits maiores
- OAuth para features premium

---

## Rate Limits

### OpenF1 API
- **Free tier**: 3 requests/second, 30 requests/minute
- **Sponsor tier**: 6 requests/second, 60 requests/minute

### Nossa API
- **Geral**: 100 requests/minute por IP
- **WebSocket**: 1 conexão por usuário

### Headers de Rate Limit

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1614556800
```

---

## Endpoints

### Telemetry

#### GET /api/telemetry/car-data

Obtém dados de telemetria dos carros.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| session_key | int | Sim | ID da sessão |
| driver_number | int | Não | Número do piloto |
| speed | int | Não | Filtro de velocidade mínima |
| limit | int | Não | Limite de resultados (default: 100) |

**Exemplo:**
```bash
curl "http://localhost:8000/api/telemetry/car-data?session_key=9161&driver_number=1&limit=10"
```

**Resposta:**
```json
[
  {
    "date": "2023-09-16T13:00:59.308000+00:00",
    "driver_number": 1,
    "meeting_key": 1219,
    "session_key": 9161,
    "speed": 285,
    "throttle": 100,
    "brake": 0,
    "gear": 8,
    "rpm": 11500,
    "drs": 1
  }
]
```

---

#### GET /api/telemetry/positions

Obtém posições dos pilotos.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| session_key | int | Sim | ID da sessão |
| driver_number | int | Não | Número do piloto |
| latest | bool | Não | Retorna apenas última posição |

**Exemplo:**
```bash
curl "http://localhost:8000/api/telemetry/positions?session_key=9161&latest=true"
```

**Resposta:**
```json
[
  {
    "date": "2023-09-16T14:30:00.000000+00:00",
    "driver_number": 1,
    "meeting_key": 1219,
    "position": 1,
    "session_key": 9161
  }
]
```

---

#### GET /api/telemetry/laps

Obtém dados de voltas.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| session_key | int | Sim | ID da sessão |
| driver_number | int | Não | Número do piloto |
| lap_number | int | Não | Número da volta |

**Exemplo:**
```bash
curl "http://localhost:8000/api/telemetry/laps?session_key=9161&driver_number=1&lap_number=1"
```

**Resposta:**
```json
[
  {
    "lap_number": 1,
    "driver_number": 1,
    "lap_duration": 95.123,
    "duration_sector_1": 30.456,
    "duration_sector_2": 32.789,
    "duration_sector_3": 31.878,
    "i1_speed": 285,
    "i2_speed": 290,
    "st_speed": 295,
    "is_pit_out_lap": false
  }
]
```

---

#### GET /api/telemetry/drivers

Obtém lista de pilotos.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| session_key | int | Sim | ID da sessão |

**Exemplo:**
```bash
curl "http://localhost:8000/api/telemetry/drivers?session_key=9161"
```

**Resposta:**
```json
[
  {
    "driver_number": 1,
    "name_acronym": "VER",
    "first_name": "Max",
    "last_name": "Verstappen",
    "team_name": "Red Bull Racing",
    "team_colour": "0600EF",
    "country_code": "NED"
  }
]
```

---

### Sessions

#### GET /api/sessions/meetings

Obtém lista de meetings (GPs).

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| year | int | Não | Ano (default: todos) |

**Exemplo:**
```bash
curl "http://localhost:8000/api/sessions/meetings?year=2024"
```

**Resposta:**
```json
[
  {
    "meeting_key": 1207,
    "meeting_name": "Bahrain Grand Prix",
    "location": "Sakhir",
    "country_name": "Bahrain",
    "circuit_short_name": "Sakhir",
    "date_start": "2023-03-03T11:30:00+00:00",
    "year": 2023
  }
]
```

---

#### GET /api/sessions/sessions

Obtém sessões de um meeting.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| meeting_key | int | Sim | ID do meeting |

**Exemplo:**
```bash
curl "http://localhost:8000/api/sessions/sessions?meeting_key=1207"
```

**Resposta:**
```json
[
  {
    "session_key": 9070,
    "session_type": "Race",
    "session_name": "Race",
    "date_start": "2023-04-30T11:00:00+00:00",
    "meeting_key": 1207
  }
]
```

---

### Fast-F1

#### POST /api/fastf1/load-session

Carrega uma sessão histórica.

**Body:**
```json
{
  "year": 2023,
  "gp": "Monaco",
  "identifier": "R"
}
```

**Resposta:**
```json
{
  "session_loaded": true,
  "session_info": {
    "name": "Monaco Grand Prix",
    "date": "2023-05-28",
    "total_laps": 78
  }
}
```

---

#### GET /api/fastf1/telemetry

Obtém telemetria de uma sessão carregada.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| driver | str | Sim | Código do piloto (ex: "VER") |

**Exemplo:**
```bash
curl "http://localhost:8000/api/fastf1/telemetry?driver=VER"
```

---

### Predictions

#### POST /api/predictions/pit-stop

Prevê pit stop de um piloto.

**Body:**
```json
{
  "session_key": 9161,
  "driver_number": 1,
  "current_lap": 20,
  "current_tyre": "MEDIUM",
  "tyre_age": 15,
  "current_position": 1
}
```

**Resposta:**
```json
{
  "driver_number": 1,
  "probability": 0.75,
  "predicted_lap": 25,
  "recommended_compound": "HARD",
  "confidence": 0.82,
  "reasons": [
    "High tyre degradation",
    "Optimal pit window approaching"
  ]
}
```

---

#### GET /api/predictions/position-forecast

Prevê posições finais.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| session_key | int | Sim | ID da sessão |
| laps_ahead | int | Não | Voltas à frente (default: 10) |

**Resposta:**
```json
{
  "session_key": 9161,
  "predictions": [
    {
      "driver_number": 1,
      "current_position": 1,
      "predicted_position": 1,
      "position_change": 0,
      "confidence": 0.95
    }
  ]
}
```

---

### Weather

#### GET /api/weather/current

Obtém clima atual.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| latitude | float | Sim | Latitude |
| longitude | float | Sim | Longitude |

**Exemplo:**
```bash
curl "http://localhost:8000/api/weather/current?latitude=26.032&longitude=50.511"
```

**Resposta:**
```json
{
  "latitude": 26.032,
  "longitude": 50.511,
  "current": {
    "temperature_2m": 32.5,
    "relative_humidity_2m": 45,
    "wind_speed_10m": 15.2,
    "precipitation": 0
  }
}
```

---

#### GET /api/weather/circuit/{circuit_name}

Obtém clima de um circuito.

**Parâmetros de URL:**
- `circuit_name`: Nome do circuito (Sakhir, Monaco, etc.)

**Exemplo:**
```bash
curl "http://localhost:8000/api/weather/circuit/Sakhir"
```

---

### F1DB

#### GET /api/f1db/drivers

Obtém pilotos históricos.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| season_year | int | Não | Ano da temporada |
| limit | int | Não | Limite (default: 50) |
| offset | int | Não | Offset (default: 0) |

**Exemplo:**
```bash
curl "http://localhost:8000/api/f1db/drivers?season_year=2023"
```

---

#### GET /api/f1db/constructors

Obtém construtores/equipes.

**Exemplo:**
```bash
curl "http://localhost:8000/api/f1db/constructors"
```

---

#### GET /api/f1db/circuits

Obtém circuitos.

**Exemplo:**
```bash
curl "http://localhost:8000/api/f1db/circuits"
```

---

#### GET /api/f1db/seasons/{year}/standings

Obtém classificação de uma temporada.

**Exemplo:**
```bash
curl "http://localhost:8000/api/f1db/seasons/2023/standings"
```

---

#### GET /api/f1db/search

Busca full-text.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| q | str | Sim | Termo de busca |

**Exemplo:**
```bash
curl "http://localhost:8000/api/f1db/search?q=Hamilton"
```

---

### Fantasy

#### POST /api/fantasy/predict/{driver_id}

Prevê pontos de um piloto.

**Parâmetros de URL:**
- `driver_id`: Número do piloto

**Query params:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| circuit_id | str | Não | ID do circuito |

**Exemplo:**
```bash
curl -X POST "http://localhost:8000/api/fantasy/predict/1?circuit_id=monaco"
```

**Resposta:**
```json
{
  "driver_id": 1,
  "driver_name": "Max Verstappen",
  "team_name": "Red Bull Racing",
  "price": 33.5,
  "expected_qualifying_position": 1,
  "expected_race_position": 1,
  "total_expected_points": 27.2,
  "points_per_million": 0.81,
  "confidence": 0.85,
  "risk_level": "low",
  "reasons": [
    "Strong pole position candidate",
    "Podium finish expected"
  ]
}
```

---

#### GET /api/fantasy/recommend

Recomenda time ótimo.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| budget | float | Não | Orçamento (default: 100.0) |
| must_include | str | Não | IDs de pilotos obrigatórios |
| exclude | str | Não | IDs de pilotos para excluir |

**Exemplo:**
```bash
curl "http://localhost:8000/api/fantasy/recommend?budget=100"
```

**Resposta:**
```json
{
  "drivers": [
    {
      "driver_id": 1,
      "driver_name": "Max Verstappen",
      "price": 33.5,
      "total_expected_points": 27.2
    }
  ],
  "constructor": {
    "name": "Red Bull Racing",
    "price": 38.5,
    "expected_points": 35.0
  },
  "total_cost": 98.5,
  "total_expected_points": 95.2,
  "remaining_budget": 1.5
}
```

---

#### GET /api/fantasy/value-plays

Obtém melhor custo/benefício.

**Parâmetros:**
| Nome | Tipo | Obrigatório | Descrição |
|------|------|-------------|-----------|
| limit | int | Não | Limite (default: 10) |

**Exemplo:**
```bash
curl "http://localhost:8000/api/fantasy/value-plays?limit=5"
```

---

#### GET /api/fantasy/compare/{driver1}/{driver2}

Compara dois pilotos.

**Exemplo:**
```bash
curl "http://localhost:8000/api/fantasy/compare/1/11"
```

---

## WebSocket

### Conexão

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Mensagens

#### Subscribe

```json
{
  "type": "subscribe",
  "session_key": 9161,
  "drivers": [1, 11, 16],
  "channels": ["telemetry", "positions"]
}
```

#### Mensagens Recebidas

**Telemetria:**
```json
{
  "type": "telemetry",
  "data": [
    {
      "driver_number": 1,
      "speed": 285,
      "throttle": 100,
      "brake": 0,
      "timestamp": 1614556800
    }
  ]
}
```

**Posições:**
```json
{
  "type": "positions",
  "data": [
    {
      "driver_number": 1,
      "position": 1,
      "timestamp": 1614556800
    }
  ]
}
```

**Heartbeat:**
```json
{
  "type": "heartbeat",
  "timestamp": 1614556800
}
```

### Exemplo de Uso

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  // Subscribe to telemetry
  ws.send(JSON.stringify({
    type: 'subscribe',
    session_key: 9161,
    drivers: [1, 11, 16],
    channels: ['telemetry', 'positions']
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'telemetry':
      console.log('Telemetry update:', message.data);
      break;
    case 'positions':
      console.log('Positions update:', message.data);
      break;
  }
};
```

---

## Erros

### Códigos HTTP

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 400 | Bad Request |
| 404 | Not Found |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

### Formato de Erro

```json
{
  "detail": "Error message here"
}
```

### Exemplos de Erro

**400 Bad Request:**
```json
{
  "detail": "session_key is required"
}
```

**404 Not Found:**
```json
{
  "detail": "Driver not found"
}
```

**429 Too Many Requests:**
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

---

## Exemplos

### JavaScript/TypeScript

```typescript
// Fetch drivers
const response = await fetch('http://localhost:8000/api/telemetry/drivers?session_key=9161');
const drivers = await response.json();

// Fetch telemetry
const telemetryResponse = await fetch(
  'http://localhost:8000/api/telemetry/car-data?session_key=9161&driver_number=1&limit=100'
);
const telemetry = await telemetryResponse.json();

// Fantasy prediction
const fantasyResponse = await fetch(
  'http://localhost:8000/api/fantasy/predict/1',
  { method: 'POST' }
);
const prediction = await fantasyResponse.json();
```

### Python

```python
import requests

# Fetch drivers
response = requests.get('http://localhost:8000/api/telemetry/drivers', params={
    'session_key': 9161
})
drivers = response.json()

# Fetch telemetry
response = requests.get('http://localhost:8000/api/telemetry/car-data', params={
    'session_key': 9161,
    'driver_number': 1,
    'limit': 100
})
telemetry = response.json()

# Fantasy prediction
response = requests.post('http://localhost:8000/api/fantasy/predict/1')
prediction = response.json()
```

### cURL

```bash
# Get drivers
curl "http://localhost:8000/api/telemetry/drivers?session_key=9161"

# Get telemetry
curl "http://localhost:8000/api/telemetry/car-data?session_key=9161&driver_number=1&limit=100"

# Get fantasy recommendation
curl "http://localhost:8000/api/fantasy/recommend?budget=100"
```

---

## SDKs e Clientes

### JavaScript/TypeScript (em breve)

```bash
npm install @f1-telemetry/client
```

```typescript
import { F1TelemetryClient } from '@f1-telemetry/client';

const client = new F1TelemetryClient({
  baseUrl: 'http://localhost:8000'
});

const drivers = await client.telemetry.getDrivers(9161);
```

### Python (em breve)

```bash
pip install f1-telemetry-client
```

```python
from f1_telemetry_client import F1TelemetryClient

client = F1TelemetryClient(base_url='http://localhost:8000')

drivers = client.telemetry.get_drivers(session_key=9161)
```

---

## Changelog

### v0.1.0 (2024-03-17)
- Initial release
- Real-time telemetry via WebSocket
- Historical data via F1DB
- ML predictions
- Weather integration
- Fantasy F1 helper

---

## Suporte

- **Issues**: [GitHub Issues](https://github.com/alissonryan/OpenF1-Telemetry-Platform/issues)
- **Docs**: [Documentation](https://github.com/alissonryan/OpenF1-Telemetry-Platform/blob/main/README.md)

---

**Feito com ❤️ para a comunidade F1** 🏎️
