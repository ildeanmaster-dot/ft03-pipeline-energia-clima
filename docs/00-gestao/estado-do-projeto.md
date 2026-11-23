# Estado do projeto

Versão 1.1 · 23/11/2026 (atualize a cada sessão de trabalho)

**Pasta local do projeto:** `D:\Portifolio\DesafioPythonFT03Projeto1` (gravada em 12/11/2026).

**Resumo (23/11/2026):** o pipeline rodou com as APIs reais no Windows (Python 3.12,
`duckdb` 2.0.0), o `output/` foi gerado e versionado e o repositório público foi criado:
https://github.com/ildeanmaster-dot/ft03-pipeline-energia-clima. Falta enviar o link pelo
formulário e validar o README num clone limpo.

## 1. Situação por etapa
| Etapa | Situação | O que falta |
|---|---|---|
| 1. Requisitos e critérios de aceite | Concluída | — |
| 2. Escolha e validação das APIs | Concluída | — |
| 3. Desenho dos dados e das regras | Concluída | — |
| 4. Estrutura do repositório | Concluída | — |
| 5. Execução ponta a ponta | Concluída | — |
| 6. Resiliência, qualidade e reprocessamento | Concluída | — |
| 7. Testes e documentação | Concluída | Validar o README num clone limpo no Windows |
| 8. Revisão e entrega | Parcial | Enviar o link pelo formulário |

## 2. Situação por componente
| Componente | Situação | Evidência |
|---|---|---|
| Configuração por ambiente (`src/pipeline/config.py`) | Implementado | Usado em todos os testes; `.env.example` |
| Cliente HTTP (`http_client.py`) | Implementado e testado | `tests/test_http_client.py` (10 testes: 429, 503, 500, 404, timeout, conexão, taxa, mascaramento) |
| Extração (`extract.py`) | Implementado, testado e executado com as APIs reais (23/11/2026) | `tests/test_extract.py` (9 testes), `tests/test_integracao_http.py` |
| Desaninhamento SQL (`sql/01_staging.sql`) | Implementado e testado | `tests/test_transform.py` (3 testes de UNNEST + amostras reais) |
| Transformações T1 a T5 (`sql/02_transform.sql`) | Implementado e testado | `tests/test_transform.py` (12 testes) |
| Qualidade (`quality.py`) | Implementado e testado | `tests/test_quality.py` (6 testes) |
| Persistência (`persist.py`) | Implementado e testado | `tests/test_persist_e_pipeline.py` (Snappy, partição, reexecução) |
| Orquestração e relatório (`main.py`) | Implementado e testado | `tests/test_persist_e_pipeline.py`, `tests/test_integracao_http.py` |
| `run.sh` | Testado em Linux | Execução numa cópia limpa em 12/11/2026 (falhou só na rede bloqueada) |
| `run.ps1` | Não testado | Escrito sem PowerShell disponível (DT-03) |
| Configuração do VS Code (`.vscode/`) | Pasta renomeada; tarefas não conferidas no VS Code | DT-04 |
| Dataset em `output/dataset/` | Gerado e versionado | 3 partições (ano=2026, mes=8, 9, 10), 44.160 linhas, Snappy |
| Relatório em `output/reports/` | Gerado e versionado | `quality_report.json`: `success_with_warnings`, 41 de 42 aprovadas, 1 aviso |
| Repositório público no GitHub | Criado (23/11/2026) | https://github.com/ildeanmaster-dot/ft03-pipeline-energia-clima |
| Portal de acompanhamento | Pendente | Aguarda decisão (P-05) |

## 3. Números (23/11/2026)
| Medida | Valor |
|---|---|
| Testes automatizados | 43, todos passando: Python 3.13 + duckdb 2.0.0 (Linux, ambiente de construção) e Python 3.12 + duckdb 1.5.6 (Linux remoto desta máquina) |
| Módulos Python em `src/pipeline/` | 7 |
| Arquivos SQL | 2 (4 desaninhamentos, 5 transformações) |
| Áreas de carga no parâmetro | 20 |
| Verificações de qualidade por execução | 42 (1 schema, 23 null ratio, 1 unicidade, 12 intervalo, 5 JOIN/volume/completude) |
| Requisitos do enunciado | ver resumo em `docs/01-negocio/requisitos.md` |
| Execuções com as APIs reais | 2 em 23/11/2026: rápida (PA, 1 dia, 24 linhas, 42 de 42) e completa (01/08 a 31/10/2026, 20 áreas, 44.160 linhas, 113 s) |
| Testes no Windows | `43 passed` (Python 3.12, `duckdb` 2.0.0) |
| Aviso da execução completa | `intervalo:participacao_mmgd_pct`: 376 horas acima de 100% (MS 238, MT 109, PI 25, RO 4; máximo 185%); valor da fonte, mantido |

## 4. O que foi conferido com dado real (12/11/2026, pelo navegador)
- ONS, outubro/2026, áreas AC, AM, AP, CE, DF, ES, GO, MA, MG, MS: 1.488 registros cada,
  48 por dia, sem nulos, sem valores negativos, sem chaves repetidas.
- ONS, área PA: período de 4 meses cortado em 107 de 122 dias; 9 meses cortado em 106 dias.
- Open-Meteo, centróide do PA, 01/08 a 31/10/2026: 2.208 horas, sem nulos nas 4 variáveis.
- Nager.Date, BR 2026: 15 feriados; regionais com a UF em `counties`.
- IBGE Malhas v4: centróide das 20 UFs do parâmetro.

## 5. Próximas ações
| # | Ação | Quem |
|---|---|---|
| 1 | Enviar o link do repositório pelo formulário antes de 23/11/2026 08h00 | Freitas |
| 2 | Clonar em outra pasta e seguir só o README (prova de reprodutibilidade, RNF-12) | Freitas |
| 3 | Conferir as tarefas do VS Code (DT-04) e o `run.ps1` (DT-03) | Freitas |
