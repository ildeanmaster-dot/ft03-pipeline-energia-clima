# Arquitetura da solução

Versão 1.0 · 12/11/2026

## 1. Visão em uma frase
Um processo Python único, executado por linha de comando, que baixa três APIs para arquivos
JSON, transforma tudo em SQL com DuckDB em memória, valida e grava Parquet particionado.
Sem servidor, sem banco instalado, sem nuvem.

## 2. Camadas
| Camada | Onde | Conteúdo | Quem grava |
|---|---|---|---|
| Bruta | `data/raw/{ons,open_meteo,nager}/*.json` | Retorno de cada chamada, sem alteração, num envelope `{"meta", "payload"}` | `extract.py` |
| Staging | Tabelas `raw_*` e `stg_*` no DuckDB (memória) | Dados lidos com schema declarado e desaninhados | `sql/01_staging.sql` |
| Transformação | Tabelas `t1_*` a `t4_*`, `carga_horaria`, `rejeitados_ons` | Uma tabela por etapa, para auditoria e contagem | `sql/02_transform.sql` |
| Final | Tabela `carga_clima_horaria` → `output/dataset/ano=/mes=/*.parquet` | Dataset entregue | `persist.py` |
| Auditoria | `output/reports/quality_report.json` | Execução e qualidade | `main.py` |

A camada bruta não é versionada (é reproduzível); a final e o relatório são.

## 3. Componentes
| Módulo | Responsabilidade única | Depende de |
|---|---|---|
| `config.py` | Ler e validar a configuração do ambiente; carregar o parâmetro de áreas | — |
| `http_client.py` | Fazer GET com limite de taxa, retentativa, timeout e erro classificado | `requests`, `urllib3` |
| `extract.py` | Conhecer cada API: URL, parâmetros, validação do retorno, gravação bruta | `config`, um cliente com `get_text` |
| `transform.py` | Definir as variáveis de caminho e executar os arquivos SQL; contar linhas por etapa | `duckdb` |
| `quality.py` | Contrato do dataset e verificações | `duckdb` |
| `persist.py` | Gravar e reler o Parquet particionado | `duckdb` |
| `main.py` | Orquestrar, montar o relatório, definir o código de saída | todos |

`extract.py` recebe o cliente por parâmetro (qualquer objeto com `get_text`). Por isso os
testes trocam o cliente por um falso sem alterar o código de extração.

## 4. Fluxo de execução
1. `main` carrega `.env`, aplica os argumentos de linha de comando e valida a configuração.
2. Limpa `data/raw/` e extrai, em sequência, ONS, Open-Meteo e Nager.Date.
3. Abre um DuckDB em memória e roda `01_staging.sql` e `02_transform.sql`.
4. Roda as verificações de qualidade sobre `carga_clima_horaria`.
5. Se nenhuma verificação de severidade "erro" falhou, apaga as partições da execução e grava o Parquet.
6. Relê o Parquet (linhas e compressão) e grava o relatório.
7. Sai com código 0 (sucesso), 1 (falha) ou 2 (configuração inválida).

Em qualquer falha, o relatório é gravado com o erro antes de sair.

## 5. Modelo de dados
- **Granularidade:** uma linha por área de carga e por hora UTC.
- **Chave:** (`cod_areacarga`, `hora_utc`).
- **Relações:** carga N:1 área (parâmetro); carga 1:0..1 clima (área, hora); carga N:0..1
  feriado (data de referência, UF).
- Colunas e origem de cada uma: `docs/03-tecnico/dicionario-de-dados.md`.

## 6. Escolhas de arquitetura
Registradas em `docs/02-arquitetura/adr.md`. Resumo:

| Escolha | Ganho | O que se abre mão |
|---|---|---|
| DuckDB em memória | Zero infraestrutura; SQL completo; grava Parquet particionado | Não guarda estado entre execuções |
| Arquivos JSON brutos | Depuração e reprocessamento sem chamar a API | Espaço em disco |
| SQL em arquivos `.sql` | Regras legíveis e avaliáveis como SQL | Variáveis passadas por `SET VARIABLE` |
| Uma tabela por etapa | Contagem e auditoria de cada transformação | Mais memória (irrelevante neste volume) |
| Extração sequencial | Respeito simples ao limite de taxa | Alguns minutos de execução |
| Substituir a partição inteira | Reexecução sem duplicar | Não serve para carga parcial de um mês |

## 7. Volume esperado
Com o padrão (20 áreas, 92 dias): 88.320 registros do ONS (20 × 92 × 48), 44.640 horas de
clima (20 × 93 × 24), 44.160 linhas finais (20 × 92 × 24). Cerca de 140 chamadas HTTP:
60 ao ONS (20 áreas × 3 meses, se nenhuma janela for dividida), 80 ao Open-Meteo
(20 áreas × 4 janelas, porque o dia a mais cai em novembro) e 1 ao Nager.Date.

## 8. O que mudaria com mais volume
Fora do escopo; registrado para orientar evolução: extração paralela com limite por API,
camada bruta por `run_id`, DuckDB em arquivo ou motor distribuído, partição por dia,
orquestrador com agendamento.
