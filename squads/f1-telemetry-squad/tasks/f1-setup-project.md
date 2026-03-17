# Task: Setup Project

## Metadata
- **Agent**: @f1-architect
- **Sprint**: 1
- **Priority**: HIGH
- **Estimate**: 4h

## Objective
Inicializar a estrutura do projeto F1 Telemetry com monorepo, configurar ambientes de desenvolvimento e estabelecer padrões de código.

## Prerequisites
- Node.js 20+ instalado
- Python 3.11+ instalado
- pnpm instalado
- Docker instalado (opcional)

## Inputs
- [ ] Requisitos do projeto (README.md)
- [ ] Tech stack definido (config/tech-stack.md)

## Outputs
- [ ] Monorepo inicializado
- [ ] Frontend (Next.js) scaffolded
- [ ] Backend (FastAPI) scaffolded
- [ ] Shared package criado
- [ ] Docker compose configurado
- [ ] CI/CD básico configurado

## Steps

### 1. Criar Monorepo
```bash
mkdir projeto-f1
cd projeto-f1
pnpm init
```

### 2. Configurar pnpm workspaces
```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

### 3. Criar estrutura de pastas
```bash
mkdir -p apps/web apps/api packages/shared
```

### 4. Scaffold Next.js App
```bash
cd apps
npx create-next-app@latest web --typescript --tailwind --eslint --app --src-dir
```

### 5. Scaffold FastAPI App
```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic httpx
```

### 6. Configurar Turborepo
```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {},
    "test": {}
  }
}
```

### 7. Configurar Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: ./apps/web
    ports:
      - "3000:3000"
    volumes:
      - ./apps/web:/app
      
  api:
    build: ./apps/api
    ports:
      - "8000:8000"
    volumes:
      - ./apps/api:/app
```

### 8. Configurar CI/CD
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install
      - run: pnpm --filter web lint
      - run: pnpm --filter web test
      
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r apps/api/requirements.txt
      - run: pytest apps/api
```

## Acceptance Criteria
- [ ] `pnpm dev` inicia frontend e backend
- [ ] Frontend acessível em localhost:3000
- [ ] Backend acessível em localhost:8000
- [ ] Hot reload funcionando
- [ ] Lint passando em ambos projetos

## Dependencies
- Nenhum (primeira tarefa)

## Risks
- Incompatibilidade de versões Node/Python
- Problemas de CORS entre frontend e backend

## Notes
- Considerar usar `create-turbo` para setup inicial mais rápido
- Configurar variáveis de ambiente desde o início
