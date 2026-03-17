# Factory/Droid Configuration

Este diretório contém a configuração para o Droid CLI (da Factory.ai).
A estrutura típica deste diretório pode incluir:

- `settings.json` ou `settings.local.json`: Configurações gerais (modelos, ferramentas, segurança, dados de telemetria).
- `mcp.json`: Configurações do Model Context Protocol (MCP) para servidores MCP.
- `prompts/`: Diretório para prompts customizados (ex: `prompts/review.md`).
- `droids/`: Diretório para os Custom Droids (subagentes especializados, definidos em arquivos Markdown com suas próprias diretrizes).

O Droid CLI reconhece esta pasta automaticamente para gerenciar o comportamento dos agentes dentro deste repositório.
