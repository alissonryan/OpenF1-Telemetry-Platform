# F1 Telemetry Platform - Contributing Guide

Obrigado pelo interesse em contribuir com o F1 Telemetry Platform! 🏎️

## Índice

- [Código de Conduta](#código-de-conduta)
- [Como Contribuir](#como-contribuir)
- [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento)
- [Padrões de Código](#padrões-de-código)
- [Processo de Pull Request](#processo-de-pull-request)
- [Reportando Bugs](#reportando-bugs)
- [Sugerindo Features](#sugerindo-features)

---

## Código de Conduta

### Nosso Compromisso

Como membros, contribuidores e líderes, nos comprometemos a fazer da participação em nossa comunidade uma experiência livre de assédio para todos, independentemente de:

- Idade, tamanho do corpo, deficiência visível ou invisível
- Etnia, características sexuais, identidade ou expressão de gênero
- Nível de experiência, educação, status socioeconômico
- Nacionalidade, aparência pessoal, raça, religião
- Identidade ou orientação sexual

### Nossos Padrões

**Comportamentos Positivos:**
- Usar linguagem acolhedora e inclusiva
- Respeitar diferentes pontos de vista e experiências
- Aceitar críticas construtivas com elegância
- Focar no que é melhor para a comunidade
- Mostrar empatia e gentileza para com outros membros

**Comportamentos Inaceitáveis:**
- Uso de linguagem ou imagens sexualizadas
- Trolling, comentários insultuosos/depreciativos
- Assédio público ou privado
- Publicar informações privadas sem permissão
- Outras condutas inapropriadas em contexto profissional

---

## Como Contribuir

### Tipos de Contribuição

1. **Código**
   - Bug fixes
   - Novas features
   - Otimizações
   - Refatoração

2. **Documentação**
   - Correções de typos
   - Melhorias na documentação
   - Traduções
   - Tutoriais

3. **Testes**
   - Testes unitários
   - Testes de integração
   - Testes E2E

4. **Design**
   - UI/UX improvements
   - Animações
   - Responsividade

---

## Ambiente de Desenvolvimento

### Pré-requisitos

```bash
# Node.js
node --version  # >= 20.0.0
npm --version   # >= 10.0.0

# Python
python3 --version  # >= 3.11
pip --version      # >= 23.0

# Git
git --version  # >= 2.30

# Opcional: Docker
docker --version
docker-compose --version
```

### Setup Inicial

```bash
# 1. Fork o repositório
# Clique em "Fork" no GitHub

# 2. Clone seu fork
git clone https://github.com/seu-usuario/OpenF1-Telemetry-Platform.git
cd OpenF1-Telemetry-Platform

# 3. Adicione upstream
git remote add upstream https://github.com/alissonryan/OpenF1-Telemetry-Platform.git

# 4. Instale dependências do frontend
npm install
cd apps/web && npm install && cd ../..

# 5. Configure o backend
cd apps/api
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
cd ../..

# 6. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# 7. Baixe dados do F1DB (opcional)
mkdir -p data/f1db
# Download de https://github.com/f1db/f1db/releases
# Extraia f1db.db para data/f1db/
```

### Rodando o Projeto

```bash
# Terminal 1: Backend
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd apps/web
npm run dev

# Terminal 3: Testes (opcional)
cd apps/api
source .venv/bin/activate
pytest --watch
```

### Verificando Tudo

```bash
# Lint
npm run lint

# Type check
npm run typecheck

# Testes
npm test
pytest

# Build
npm run build
```

---

## Padrões de Código

### TypeScript/Frontend

```typescript
// Use interfaces para tipos
interface Driver {
  id: number;
  name: string;
  team: string;
}

// Prefira arrow functions
const getDriver = (id: number): Driver => {
  return drivers.find(d => d.id === id);
};

// Use async/await
const fetchDriver = async (id: number): Promise<Driver> => {
  const response = await fetch(`/api/drivers/${id}`);
  return response.json();
};

// Componentes funcionais
export const DriverCard: React.FC<{ driver: Driver }> = ({ driver }) => {
  return (
    <div className="p-4 rounded-lg bg-gray-800">
      <h3>{driver.name}</h3>
      <p>{driver.team}</p>
    </div>
  );
};

// Use Tailwind CSS
<div className="flex flex-col gap-4 p-6">
  <h1 className="text-2xl font-bold text-white">
    Dashboard
  </h1>
</div>

// Hooks customizados
const useDriver = (id: number) => {
  const [driver, setDriver] = useState<Driver | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchDriver(id).then(setDriver).finally(() => setLoading(false));
  }, [id]);
  
  return { driver, loading };
};
```

### Python/Backend

```python
# Use type hints
from typing import List, Optional
from pydantic import BaseModel

class Driver(BaseModel):
    id: int
    name: str
    team: str

# Use async/await
async def get_driver(driver_id: int) -> Optional[Driver]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/drivers/{driver_id}")
        if response.status_code == 200:
            return Driver(**response.json())
    return None

# Use dependency injection
from fastapi import Depends

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/drivers/{driver_id}")
async def read_driver(
    driver_id: int,
    db: Session = Depends(get_db)
) -> Driver:
    return db.query(DriverModel).filter(DriverModel.id == driver_id).first()

# Use Pydantic models
class DriverCreate(BaseModel):
    name: str
    team: str
    number: int

@router.post("/drivers")
async def create_driver(driver: DriverCreate) -> Driver:
    # ...
```

### Git Commits

```bash
# Formato: tipo(escopo): descrição

# Tipos:
# feat: Nova feature
# fix: Bug fix
# docs: Documentação
# style: Formatação
# refactor: Refatoração
# test: Testes
# chore: Manutenção

# Exemplos:
git commit -m "feat: Add driver comparison feature"
git commit -m "fix: Fix WebSocket reconnection bug"
git commit -m "docs: Update API documentation"
git commit -m "refactor(api): Improve database queries"
git commit -m "test(fantasy): Add unit tests for predictor"
```

### Estrutura de Arquivos

```
projeto-f1/
├── apps/
│   ├── api/                    # Backend FastAPI
│   │   ├── app/
│   │   │   ├── routers/        # API endpoints
│   │   │   ├── services/       # Business logic
│   │   │   ├── models/         # Pydantic models
│   │   │   └── ml/             # ML models
│   │   └── tests/              # Testes
│   │
│   └── web/                    # Frontend Next.js
│       └── src/
│           ├── app/            # Páginas (App Router)
│           ├── components/     # Componentes React
│           ├── hooks/          # Custom hooks
│           ├── stores/         # Zustand stores
│           └── types/          # TypeScript types
│
├── packages/shared/            # Tipos compartilhados
├── data/                       # Dados (F1DB, circuits)
└── docs/                       # Documentação
```

---

## Processo de Pull Request

### 1. Crie uma Branch

```bash
# Atualize main
git checkout main
git pull upstream main

# Crie branch
git checkout -b feature/nova-feature
# ou
git checkout -b fix/corrigir-bug
```

### 2. Faça suas Mudanças

```bash
# Faça commits pequenos e focados
git add .
git commit -m "feat: Add new feature"

# Mantenha atualizado com upstream
git fetch upstream
git rebase upstream/main
```

### 3. Teste suas Mudanças

```bash
# Rode testes
npm test
pytest

# Verifique lint
npm run lint

# Verifique types
npm run typecheck

# Build
npm run build
```

### 4. Push e Crie PR

```bash
# Push para seu fork
git push origin feature/nova-feature

# Vá ao GitHub e clique em "Create Pull Request"
```

### 5. Template de PR

```markdown
## Descrição
Descrição clara do que foi feito.

## Tipo de Mudança
- [ ] Bug fix (non-breaking change)
- [ ] Nova feature (non-breaking change)
- [ ] Breaking change (fix ou feature que muda API)
- [ ] Documentação

## Checklist
- [ ] Código segue padrões do projeto
- [ ] Testes adicionados/atualizados
- [ ] Documentação atualizada
- [ ] Sem warnings no lint
- [ ] Build passando

## Screenshots (se aplicável)
Screenshots aqui.

## Issues Relacionadas
Closes #123
```

### 6. Review

- Responda a todos os comentários
- Faça as mudanças solicitadas
- Mantenha a discussão respeitosa
- Seja paciente

---

## Reportando Bugs

### Antes de Reportar

1. Verifique se já existe uma issue similar
2. Teste com a versão mais recente
3. Colete informações relevantes

### Template de Bug Report

```markdown
## Descrição
Descrição clara do bug.

## Passos para Reproduzir
1. Vá para '...'
2. Clique em '...'
3. Veja erro

## Comportamento Esperado
O que deveria acontecer.

## Comportamento Atual
O que acontece.

## Screenshots
Se aplicável.

## Ambiente
- OS: [e.g., macOS, Windows, Linux]
- Browser: [e.g., Chrome, Safari]
- Version: [e.g., 22]
- Node: [e.g., 20.0.0]
- Python: [e.g., 3.11]

## Logs
```
Cole logs relevantes aqui
```

## Contexto Adicional
Qualquer outra informação.
```

---

## Sugerindo Features

### Template de Feature Request

```markdown
## Problema
Descrição do problema que a feature resolve.

## Solução Proposta
Como você imagina que a feature funcionaria.

## Alternativas Consideradas
Outras soluções que você considerou.

## Exemplos
Exemplos de como a feature seria usada.

## Contexto Adicional
Screenshots, mockups, etc.

## Would you be willing to submit a PR?
- [ ] Yes, I'd like to submit a PR for this
```

---

## Recursos Úteis

### Documentação
- [Next.js Docs](https://nextjs.org/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [OpenF1 API](https://openf1.org/)
- [Fast-F1 Docs](https://docs.fastf1.dev/)

### Tutoriais
- [Next.js Tutorial](https://nextjs.org/learn)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)

### Ferramentas
- [VS Code](https://code.visualstudio.com/)
- [Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [ESLint Extension](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)
- [Prettier Extension](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)

---

## Contato

- **Issues**: [GitHub Issues](https://github.com/alissonryan/OpenF1-Telemetry-Platform/issues)
- **Discussões**: [GitHub Discussions](https://github.com/alissonryan/OpenF1-Telemetry-Platform/discussions)
- **Email**: seu-email@example.com

---

## Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a licença MIT.

---

**Obrigado por contribuir!** 🏎️💚
