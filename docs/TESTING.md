# F1 Telemetry Platform - Localhost Testing Guide

Guia completo para testar o projeto localmente.

## Pré-requisitos

```bash
# Verificar versões
node --version    # >= 20.0.0
python3 --version # >= 3.11
npm --version     # >= 10.0.0
git --version     # >= 2.30
```

---

## Setup Inicial

### 1. Clone e Instale Dependências

```bash
# Clone o repositório
git clone https://github.com/alissonryan/OpenF1-Telemetry-Platform.git
cd OpenF1-Telemetry-Platform

# Instale dependências do frontend
npm install
cd apps/web && npm install && cd ../..

# Configure o backend
cd apps/api
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cd ../..
```

### 2. Configure Variáveis de Ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite com suas configurações
nano .env  # ou use seu editor preferido
```

**Conteúdo do .env:**
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
MODELS_DIR=./data/models
```

### 3. Baixe Dados do F1DB (Opcional)

```bash
# Crie diretório
mkdir -p data/f1db

# Download da última release
# Vá para: https://github.com/f1db/f1db/releases
# Baixe f1db-sqlite.zip
# Extraia f1db.db para data/f1db/
```

---

## Rodando o Projeto

### Opção 1: Terminais Separados

**Terminal 1 - Backend:**
```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd apps/web
npm run dev
```

### Opção 2: Script Unificado

```bash
# Na raiz do projeto
npm run dev
```

### Opção 3: Docker

```bash
docker-compose up
```

---

## Verificando se Funcionou

### Backend

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "version": "0.1.0"}

# Check API docs
open http://localhost:8000/docs
```

### Frontend

```bash
# Acesse no browser
open http://localhost:3000

# Expected:
# - Home page com links para Dashboard e Predictions
```

---

## Testando Endpoints

### 1. OpenF1 API

```bash
# Get meetings
curl "http://localhost:8000/api/sessions/meetings" | jq

# Get sessions
curl "http://localhost:8000/api/sessions/sessions?meeting_key=1207" | jq

# Get drivers
curl "http://localhost:8000/api/telemetry/drivers?session_key=9070" | jq

# Get car data
curl "http://localhost:8000/api/telemetry/car-data?session_key=9070&driver_number=1&limit=10" | jq
```

### 2. Weather API

```bash
# Current weather
curl "http://localhost:8000/api/weather/current?latitude=26.032&longitude=50.511" | jq

# Circuit weather
curl "http://localhost:8000/api/weather/circuit/Sakhir" | jq

# Parse weather code
curl "http://localhost:8000/api/weather/parse-code/0" | jq
```

### 3. F1DB API

```bash
# Get drivers
curl "http://localhost:8000/api/f1db/drivers?season_year=2023&limit=10" | jq

# Get constructors
curl "http://localhost:8000/api/f1db/constructors" | jq

# Get circuits
curl "http://localhost:8000/api/f1db/circuits" | jq

# Get standings
curl "http://localhost:8000/api/f1db/seasons/2023/standings" | jq

# Search
curl "http://localhost:8000/api/f1db/search?q=Hamilton" | jq
```

### 4. Predictions API

```bash
# Pit stop prediction
curl -X POST "http://localhost:8000/api/predictions/pit-stop" \
  -H "Content-Type: application/json" \
  -d '{
    "session_key": 9070,
    "driver_number": 1,
    "current_lap": 20,
    "current_tyre": "MEDIUM",
    "tyre_age": 15,
    "current_position": 1
  }' | jq

# Position forecast
curl "http://localhost:8000/api/predictions/position-forecast?session_key=9070" | jq
```

### 5. Fantasy API

```bash
# Predict driver points
curl -X POST "http://localhost:8000/api/fantasy/predict/1" | jq

# Predict all drivers
curl -X POST "http://localhost:8000/api/fantasy/predict/all" | jq

# Get team recommendation
curl "http://localhost:8000/api/fantasy/recommend?budget=100" | jq

# Get value plays
curl "http://localhost:8000/api/fantasy/value-plays?limit=5" | jq

# Compare drivers
curl "http://localhost:8000/api/fantasy/compare/1/11" | jq

# Get prices
curl "http://localhost:8000/api/fantasy/prices" | jq
```

---

## Testando WebSocket

### JavaScript (Browser Console)

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected!');
  
  // Subscribe
  ws.send(JSON.stringify({
    type: 'subscribe',
    session_key: 9070,
    drivers: [1, 11, 16],
    channels: ['telemetry', 'positions']
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message.type, message.data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

### Python

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as ws:
        # Subscribe
        await ws.send(json.dumps({
            'type': 'subscribe',
            'session_key': 9070,
            'drivers': [1, 11, 16],
            'channels': ['telemetry']
        }))
        
        # Receive messages
        for i in range(10):
            message = await ws.recv()
            print(f"Received: {message}")

asyncio.run(test_websocket())
```

### cURL (wscat)

```bash
# Install wscat
npm install -g wscat

# Connect
wscat -c ws://localhost:8000/ws

# Send subscribe message
> {"type": "subscribe", "session_key": 9070, "drivers": [1], "channels": ["telemetry"]}
```

---

## Testando Frontend

### Dashboard

1. Acesse http://localhost:3000/dashboard
2. Selecione um meeting no dropdown
3. Selecione uma sessão
4. Veja os drivers carregarem
5. Selecione drivers para ver telemetria
6. Observe os gráficos atualizando

### Predictions

1. Acesse http://localhost:3000/predictions
2. Selecione uma sessão
3. Veja as previsões de pit stop
4. Veja o forecast de posições
5. Analise as estratégias

### Fantasy (quando implementado)

1. Acesse http://localhost:3000/fantasy
2. Veja as previsões de pontos
3. Monte seu time
4. Compare drivers

---

## Debugging

### Backend Logs

```bash
# Ver logs do backend
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --log-level debug
```

### Frontend Logs

```bash
# Ver logs do Next.js
cd apps/web
npm run dev

# Ou com debug
NODE_OPTIONS='--inspect' npm run dev
```

### Database

```bash
# Verificar F1DB
sqlite3 data/f1db/f1db.db

sqlite> .tables
sqlite> SELECT * FROM drivers LIMIT 5;
sqlite> .quit
```

---

## Troubleshooting

### Erro: "Module not found"

```bash
# Reinstale dependências
rm -rf node_modules package-lock.json
npm install

# Reinstale Python deps
cd apps/api
source .venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### Erro: "Port 8000 already in use"

```bash
# Encontre o processo
lsof -i :8000

# Mate o processo
kill -9 <PID>
```

### Erro: "CORS error"

```bash
# Verifique .env
CORS_ORIGINS=["http://localhost:3000"]

# Reinicie o backend
```

### Erro: "Database not found"

```bash
# Baixe F1DB
mkdir -p data/f1db
# Download de https://github.com/f1db/f1db/releases
```

### WebSocket não conecta

```bash
# Verifique se backend está rodando
curl http://localhost:8000/health

# Verifique URL do WebSocket
# Deve ser ws://localhost:8000/ws (não wss)
```

---

## Testes Automatizados

### Backend

```bash
cd apps/api
source .venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_api_integration.py -v
```

### Frontend

```bash
cd apps/web

# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Run E2E tests
npm run e2e
```

---

## Performance Testing

### Load Test (k6)

```javascript
// load-test.js
import http from 'k6/http';

export default function() {
  http.get('http://localhost:8000/api/telemetry/drivers?session_key=9070');
  http.get('http://localhost:8000/api/sessions/meetings');
}
```

```bash
# Run load test
k6 run load-test.js
```

### Stress Test

```bash
# Install wrk
brew install wrk  # Mac
# sudo apt install wrk  # Linux

# Run stress test
wrk -t12 -c400 -d30s http://localhost:8000/health
```

---

## Próximos Passos

1. **Explore a API** em http://localhost:8000/docs
2. **Teste o Dashboard** em http://localhost:3000/dashboard
3. **Veja Predictions** em http://localhost:3000/predictions
4. **Leia a Documentação** em docs/API.md
5. **Contribua** seguindo CONTRIBUTING.md

---

## Suporte

- **Issues**: https://github.com/alissonryan/OpenF1-Telemetry-Platform/issues
- **Docs**: README.md, docs/API.md
- **Email**: seu-email@example.com

---

**Happy Testing!** 🏎️💨
