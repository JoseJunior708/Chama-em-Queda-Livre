# Chama em Queda Livre: frontend

Combustão em microgravidade · dados abertos da NASA. Projecto independente; não é um produto oficial da NASA.

React, TypeScript, Tailwind v4 e Recharts.

## Correr

```bash
npm install
npm run dev      # servidor de desenvolvimento
npm run build    # verificação de tipos e build
npm run lint     # oxlint
```

## Dados

Sem configuração, a aplicação usa os dados de demonstração de `src/data/demo.ts`, que têm a
mesma forma das respostas do Backend (`resposta`, `fontes`, `verificacao`).

Para usar a API real, copia `.env.example` para `.env` e define `VITE_API_URL`. A troca é feita
em `src/api/client.ts`; os componentes não mudam.

## Estrutura

- `src/index.css`: tokens de desenho (cores, raios, tipografia) e modo claro.
- `src/types/api.ts`: formas das respostas do Backend.
- `src/api/`: cliente e hook de estados (carregar, erro, ok).
- `src/lib/experiencias.ts`: junta documentos e extracções e converte unidades (% O2, kPa, cm/s).
- `src/pages/`: Visão Geral, Experiências, Conclusões, Resumos e Assistente.
- `src/components/`: mapa de inflamabilidade, tabela, filtros, citações e painéis.
