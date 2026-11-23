# Estado do projeto

Versão 1.0 · 12/11/2026 (atualize a cada sessão de trabalho)

**Pasta local do projeto:** `D:\Portifolio\DesafioPythonFT03Projeto1` (gravada em 12/11/2026).

**Atenção (12/11/2026):** nesta máquina (Intel Core i7-870, sem AVX) o `duckdb` 2.0.0 falhou no Linux da sessão remota; o 1.5.6 funcionou. Antes de tudo, faça o teste do passo 9 de `docs/03-tecnico/guia-vscode.md` (DT-15, P-08). A pasta `_vscode` precisa ser renomeada para `.vscode` (P-09).

**Resumo:** o código, os testes e a documentação estão prontos. O pipeline **ainda não rodou
com as APIs reais**; por isso `output/` (Parquet e relatório) não existe e o repositório não
foi publicado. Essas são as duas coisas que faltam para a entrega.

## 1. Situação por etapa
| Etapa | Situação | O que falta |
|---|---|---|
| 1. Requisitos e critérios de aceite | Concluída | — |
| 2. Escolha e validação das APIs | Concluída | — |
| 3. Desenho dos dados e das regras | Concluída | — |
| 4. Estrutura do repositório | Concluída | Criar o repositório Git local e o remoto no GitHub |
| 5. Execução ponta a ponta | Parcial | Rodar com as APIs reais (só rodou com servidor local de teste) |
| 6. Resiliência, qualidade e reprocessamento | Concluída em teste | Confirmar na execução real |
| 7. Testes e documentação | Concluída | Validar o README num clone limpo no Windows |
| 8. Revisão e entrega | Pendente | Conferir `output/`, publicar, enviar o link |

## 2. Situação por componente
| Componente | Situação | Evidência |
|---|---|---|
| Configuração por ambiente (`src/pipeline/config.py`) | Implementado | Usado em todos os testes; `.env.example` |
| Cliente HTTP (`http_client.py`) | Implementado e testado | `tests/test_http_client.py` (10 testes: 429, 503, 500, 404, timeout, conexão, taxa, mascaramento) |
| Extração (`extract.py`) | Implementado e testado sem as APIs | `tests/test_extract.py` (9 testes), `tests/test_integracao_http.py` |
| Desaninhamento SQL (`sql/01_staging.sql`) | Implementado e testado | `tests/test_transform.py` (3 testes de UNNEST + amostras reais) |
| Transformações T1 a T5 (`sql/02_transform.sql`) | Implementado e testado | `tests/test_transform.py` (12 testes) |
| Qualidade (`quality.py`) | Implementado e testado | `tests/test_quality.py` (6 testes) |
| Persistência (`persist.py`) | Implementado e testado | `tests/test_persist_e_pipeline.py` (Snappy, partição, reexecução) |
| Orquestração e relatório (`main.py`) | Implementado e testado | `tests/test_persist_e_pipeline.py`, `tests/test_integracao_http.py` |
| `run.sh` | Testado em Linux | Execução numa cópia limpa em 12/11/2026 (falhou só na rede bloqueada) |
| `run.ps1` | Não testado | Escrito sem PowerShell disponível (DT-03) |
| Configuração do VS Code (`.vscode/`) | Não testado no VS Code | JSON válido; abrir e conferir (DT-04) |
| Dataset em `output/dataset/` | Pendente | Depende da execução real |
| Relatório em `output/reports/` | Pendente | Depende da execução real |
| Repositório público no GitHub | Pendente | Precisa de confirmação do responsável |
| Portal de acompanhamento | Pendente | Aguarda decisão (P-05) |

## 3. Números (12/11/2026)
| Medida | Valor |
|---|---|
| Testes automatizados | 43, todos passando: Python 3.13 + duckdb 2.0.0 (Linux, ambiente de construção) e Python 3.12 + duckdb 1.5.6 (Linux remoto desta máquina) |
| Módulos Python em `src/pipeline/` | 7 |
| Arquivos SQL | 2 (4 desaninhamentos, 5 transformações) |
| Áreas de carga no parâmetro | 20 |
| Verificações de qualidade por execução | 42 (1 schema, 23 null ratio, 1 unicidade, 12 intervalo, 5 JOIN/volume/completude) |
| Requisitos do enunciado | ver resumo em `docs/01-negocio/requisitos.md` |
| Execuções com as APIs reais | 0 |

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
| 0 | Renomear `_vscode` para `.vscode`; conferir `python --version` (3.11+); testar `import duckdb` (guia, passos 2, 3 e 9) | Freitas |
| 1 | Abrir a pasta no VS Code e rodar a tarefa "3. Rodar testes" (esperado: 43 passed) | Freitas |
| 2 | Rodar "4. Pipeline: teste rápido (PA, 1 dia)" e conferir `status: success` no relatório | Freitas |
| 3 | Rodar "5. Pipeline: execução completa" (20 áreas, 01/08 a 31/10/2026) | Freitas |
| 4 | Conferir `output/` e o relatório com `docs/00-gestao/checklist-de-entrega.md` | Freitas |
| 5 | `git init`, primeiro commit, criar o repositório público e enviar | Freitas (ou assistente, com confirmação) |
| 6 | Clonar em outra pasta e seguir só o README (prova de reprodutibilidade) | Freitas |
| 7 | Enviar o link pelo formulário antes de 23/11/2026 08h00 | Freitas |
