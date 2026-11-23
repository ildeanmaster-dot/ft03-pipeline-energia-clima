# Documentação do projeto

Versão 1.1 · 23/11/2026

Por onde começar:

- **Quero entender o projeto sem termos técnicos** → `01-negocio/visao-geral.md`
- **Vou continuar o desenvolvimento** → `00-gestao/estado-do-projeto.md` e `03-tecnico/guia-vscode.md`
- **Vou avaliar a entrega** → `01-negocio/requisitos.md` e `00-gestao/checklist-de-entrega.md`

## Mapa

| Pasta | Documento | Para que serve |
|---|---|---|
| `00-gestao` | `termo-de-abertura.md` | Objetivo, escopo, entregas, premissas, restrições, marcos |
| | `estado-do-projeto.md` | Situação por etapa e por componente, números, próximas ações |
| | `decisoes-e-pendencias.md` | Decisões tomadas (D-xx) e pendências abertas (P-xx) |
| | `roadmap.md` | Cronograma até 23/11/2026 e o que já foi adiantado |
| | `riscos.md` | Riscos e resposta a cada um |
| | `debito-tecnico.md` | Débitos conhecidos (DT-xx), impacto e ação |
| | `observacoes-e-licoes.md` | O que foi descoberto em teste ou na documentação (OB-xx) |
| | `custos-e-licencas.md` | Custo das APIs e licenças de dados e bibliotecas |
| | `checklist-de-entrega.md` | Conferência final antes de enviar o link |
| `01-negocio` | `visao-geral.md` | Explicação não técnica: pergunta, fontes, resultado |
| | `requisitos.md` | Requisitos do enunciado (RF/RNF) com status e evidência |
| | `regras-de-negocio.md` | Regras (RN-xx) com origem, status e local no código |
| | `glossario.md` | Termos de energia, clima e engenharia de dados usados aqui |
| `02-arquitetura` | `arquitetura-da-solucao.md` | Componentes, camadas, fluxo, escolhas |
| | `diagramas.md` | Diagramas Mermaid (contexto, fluxo, modelo, sequência, falhas) |
| | `adr.md` | Registro das decisões de arquitetura |
| `03-tecnico` | `guia-vscode.md` | Preparar o ambiente, rodar, depurar e testar no VS Code |
| | `fontes-de-dados.md` | As três APIs e o parâmetro de áreas, com fatos conferidos |
| | `pipeline.md` | Cada módulo e cada etapa do SQL |
| | `dicionario-de-dados.md` | Colunas do dataset final e das tabelas intermediárias |
| | `qualidade-de-dados.md` | Verificações, severidade, formato do relatório |
| | `testes.md` | O que cada teste cobre e como rodar |
| | `operacao.md` | Execução, reprocessamento e solução de problemas |
| | `seguranca.md` | Credenciais, o que não vai para o Git, dados publicados |

Fora de `docs/`: `README.md` (instruções de execução exigidas pelo enunciado), `CLAUDE.md`
(contexto para assistente no VS Code), `CHANGELOG.md`, `insumos/README.md`.

## Convenções
- Todo documento tem versão e data no topo; mudanças vão para o `CHANGELOG.md`.
- **Status por evidência:** "Implementado" só com o local no código e o teste.
- Fato de API ou biblioteca traz a fonte e a data da conferência. O que não foi conferido
  está marcado **[a validar]**.
- Classe de cada dado: **Origem** (veio da API), **Cálculo** (fórmula rastreável),
  **Parâmetro** (arquivo versionado com fonte). Não há dado inferido.