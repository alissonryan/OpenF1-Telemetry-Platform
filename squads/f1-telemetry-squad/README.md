# F1 Telemetry Squad

> Squad especializado para criar uma plataforma inovadora de telemetria F1 em tempo real com engine de predições usando Machine Learning.

## Visão do Projeto

Criar uma plataforma web **disruptiva** que combina:
- **Dashboard de Telemetria em Tempo Real** - Visualização live de dados durante corridas
- **F1 Prediction Engine** - Machine Learning para prever pit stops, posições e estratégias

## Stack Tecnológica

### Frontend
| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| Next.js | 14+ | Framework React com SSR/SSG |
| React | 18+ | UI Library |
| TypeScript | 5+ | Type Safety |
| Tailwind CSS | 3.4+ | Styling |
| Framer Motion | 11+ | Animações fluidas |
| Recharts | 2.12+ | Gráficos interativos |
| React Query | 5+ | Data fetching & caching |
| Zustand | 4.5+ | State management |
| Socket.io Client | 4.7+ | Real-time communication |

### Backend
| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| FastAPI | 0.109+ | Python API Framework |
| Fast-F1 | 3.4+ | F1 data library |
| Pandas | 2.2+ | Data manipulation |
| NumPy | 1.26+ | Numerical computing |
| Uvicorn | 0.27+ | ASGI Server |
| WebSockets | 12+ | Real-time bidirectional |

### Machine Learning
| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| scikit-learn | 1.4+ | ML algorithms |
| XGBoost | 2.0+ | Gradient boosting |
| Pydantic | 2.6+ | Data validation |

### APIs Integradas
- **OpenF1 API** (openf1.org) - Telemetria em tempo real a 3.7Hz
- **Fast-F1** - Análise de dados históricos com Pandas DataFrames

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                        │
├─────────────────────────────────────────────────────────────────┤
│  Dashboard Real-Time  │  Prediction Engine UI  │  Mobile View   │
│  - Framer Motion      │  - Interactive Charts  │  - Responsive  │
│  - WebSocket Client   │  - ML Insights         │  - Touch UI    │
└─────────────────────┬───────────────────────────────────────────┘
                      │ WebSocket / REST
┌─────────────────────▼───────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
├─────────────────────────────────────────────────────────────────┤
│  Real-Time Service    │  ML Service           │  Data Service   │
│  - WebSocket Server   │  - Prediction Models  │  - Fast-F1      │
│  - Event Streaming    │  - Model Inference    │  - Data Transform│
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                      EXTERNAL APIs                               │
├──────────────────────────┬──────────────────────────────────────┤
│      OpenF1 API          │         Fast-F1 Library              │
│  - Real-time telemetry   │    - Historical data                 │
│  - 3.7Hz car data        │    - Lap analysis                    │
│  - Position (4s)         │    - Telemetry extraction            │
│  - Weather/Pit/Stints    │    - Caching built-in                │
└──────────────────────────┴──────────────────────────────────────┘
```

## Agentes do Squad

### 1. F1 Architect (`f1-architect`)
**Responsável por:** Arquitetura do sistema e decisões técnicas
- Design da arquitetura completa
- Integração das APIs (OpenF1 + Fast-F1)
- Padrões de comunicação real-time
- Estratégia de caching
- Performance optimization

### 2. F1 Data Engineer (`f1-data-engineer`)
**Responsável por:** Pipeline de dados e database
- Design do schema de dados
- ETL pipelines para dados históricos
- Integração com Fast-F1
- Data validation e qualidade
- Caching strategy

### 3. F1 Frontend Developer (`f1-frontend-dev`)
**Responsável por:** Interface e visualizações
- Dashboard em tempo real
- Gráficos interativos com Recharts
- Animações com Framer Motion
- Design responsivo mobile/desktop
- WebSocket integration no frontend

### 4. F1 ML Engineer (`f1-ml-engineer`)
**Responsável por:** Machine Learning e predições
- Modelos de predição de pit stops
- Forecast de posições finais
- Análise de estratégias
- Feature engineering
- Model training e evaluation

### 5. F1 QA (`f1-qa`)
**Responsável por:** Qualidade e testes
- Testes de integração das APIs
- Testes de performance real-time
- Validação de dados ML
- E2E testing
- Monitoring e alerting

## Fluxo de Desenvolvimento

### Fase 1: Setup & Arquitetura (Sprint 1-2)
1. Setup do projeto (monorepo)
2. Configuração das APIs
3. Design da arquitetura
4. Database schema

### Fase 2: Core Features (Sprint 3-5)
1. Conexão OpenF1 real-time
2. Dashboard básico
3. Integração Fast-F1
4. Visualizações iniciais

### Fase 3: ML Engine (Sprint 6-8)
1. Feature engineering
2. Modelos de predição
3. Training pipeline
4. API de predições

### Fase 4: Polish & Deploy (Sprint 9-10)
1. Animações avançadas
2. Otimização de performance
3. Mobile responsiveness
4. Deploy e CI/CD

## Desafios Técnicos Identificados

### 1. Latência Real-Time
**Problema:** OpenF1 atualiza a 3.7Hz, posição a cada 4s
**Solução:** WebSocket streaming + client-side interpolation

### 2. Volume de Dados Históricos
**Problema:** Fast-F1 pode retornar grandes datasets
**Solução:** Caching agressivo + pagination + lazy loading

### 3. ML em Tempo Real
**Problema:** Predições precisam ser rápidas durante a corrida
**Solução:** Modelos pré-treinados + inference otimizada + feature caching

### 4. Animações Responsivas
**Problema:** 60fps com dados atualizando constantemente
**Solução:** React.memo + virtualization + requestAnimationFrame

### 5. Rate Limiting OpenF1
**Problema:** 30 requests/minuto no free tier
**Solução:** WebSocket connection + smart polling fallback

## Comandos do Squad

Use o prefixo `*f1-` para acessar os comandos:

### Setup
- `*f1-setup-project` - Inicializar projeto completo
- `*f1-connect-openf1` - Configurar conexão OpenF1
- `*f1-connect-fastf1` - Configurar Fast-F1

### Development
- `*f1-build-dashboard` - Criar dashboard real-time
- `*f1-create-charts` - Criar gráficos de telemetria
- `*f1-build-prediction` - Criar engine de predição

### ML
- `*f1-train-models` - Treinar modelos ML
- `*f1-optimize-performance` - Otimizar performance

### Deploy
- `*f1-deploy` - Deploy da plataforma

## Estrutura de Pastas

```
projeto-f1/
├── apps/
│   ├── web/                    # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── stores/
│   │   │   └── lib/
│   │   └── public/
│   └── api/                    # FastAPI backend
│       ├── app/
│       │   ├── routers/
│       │   ├── services/
│       │   ├── models/
│       │   └── ml/
│       └── tests/
├── packages/
│   ├── shared/                 # Tipos e utilitários compartilhados
│   └── ml-models/              # Modelos ML treinados
├── data/
│   ├── cache/                  # Cache do Fast-F1
│   └── models/                 # Modelos serializados
└── squads/
    └── f1-telemetry-squad/     # Este squad
```

## Contribuindo

Este é um projeto open-source! Veja o roadmap e pegue uma issue.

## Licença

MIT License - Use livremente para seus projetos F1!
