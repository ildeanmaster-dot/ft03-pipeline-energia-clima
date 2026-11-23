# Pipeline: módulos e etapas

Versão 1.0 · 12/11/2026

## 1. Módulos Python (`src/pipeline/`)

### `config.py`
| Elemento | O que faz |
|---|---|
| `Settings` | Configuração imutável da execução (período, áreas, pastas, parâmetros HTTP, chave opcional) |
| `Area` | Área de carga com UF e coordenada |
| `load_settings(env)` | Lê o ambiente, aplica os padrões e valida; levanta `ConfigError` com mensagem clara |
| `load_areas(arquivo, selecionadas)` | Lê `config/areas_carga.csv`; área desconhecida é erro |

### `http_client.py`
| Elemento | O que faz |
|---|---|
| `RateLimiter` | Garante o intervalo mínimo entre chamadas; soma o tempo esperado |
| `build_retry` | `urllib3.Retry`: até N tentativas para 429/500/502/503/504, conexão e leitura; backoff com jitter; `Retry-After` até 120 s |
| `HttpClient.get_text` | GET com timeout; devolve o texto ou levanta `TransientHTTPError` / `PermanentHTTPError` |
| `HttpStats` | Requisições, retentativas e bytes, levados ao relatório |
| `redact` | Mascara `apikey`, `token` e semelhantes em URLs e mensagens |

### `extract.py`
| Elemento | O que faz |
|---|---|
| `month_windows` | Divide o período em janelas que não cruzam a virada de mês |
| `parse_json_tolerant` | Lê JSON; repara valor ausente para `null` |
| `fetch_ons_window` | Busca uma janela do ONS e garante a cobertura dos dias, dividindo quando preciso |
| `extract_ons`, `extract_open_meteo`, `extract_nager` | Uma função por API; gravam a camada bruta e devolvem `SourceStats` |
| `validate_open_meteo` | Confere a estrutura horária e a quantidade de horas |
| `write_raw` | Grava o envelope de forma atômica (arquivo temporário e renomeação) |
| `reset_raw_dir` | Limpa a camada bruta no início da execução |

### `transform.py`
`run_transformations` define quatro variáveis no DuckDB (`raw_ons_glob`, `raw_clima_glob`,
`raw_feriados_glob`, `areas_file`), executa os dois arquivos SQL em ordem e devolve a
contagem de linhas de 14 tabelas (`STAGE_TABLES`).

### `quality.py`
`CONTRACT` (23 colunas com tipo, limite de nulos e intervalo) e as funções `check_schema`,
`null_ratios`, `check_nulls`, `check_uniqueness`, `check_ranges`, `check_join_and_volume`,
reunidas em `run_quality_checks`. Detalhes em `docs/03-tecnico/qualidade-de-dados.md`.

### `persist.py`
`write_partitioned` apaga as partições da execução e grava com
`COPY ... (FORMAT parquet, COMPRESSION snappy, PARTITION_BY (ano, mes), OVERWRITE_OR_IGNORE)`.
`verify_dataset` relê o que foi gravado e devolve o total de linhas e os codecs encontrados.

### `main.py`
`run_pipeline` executa as etapas, monta o relatório e garante a gravação dele no bloco
`finally`. `main` trata os argumentos (`--inicio`, `--fim`, `--areas`, `--skip-extract`) e
devolve o código de saída: 0 sucesso, 1 falha, 2 configuração inválida.

## 2. SQL — `sql/01_staging.sql`

Lê a camada bruta com **schema declarado** (campo de tipo inesperado falha na leitura) e desaninha.

| Tabela | Origem | Operação |
|---|---|---|
| `dim_areas` | `config/areas_carga.csv` | Leitura com tipos declarados |
| `raw_ons` | `data/raw/ons/*.json` | Um arquivo por linha; `payload` é um array de structs |
| `stg_ons` | `raw_ons` | **UNNEST 1:** `unnest(payload, recursive := true)` → uma linha por registro, um campo por coluna |
| `raw_clima` | `data/raw/open_meteo/*.json` | `payload.hourly` com cinco arrays |
| `stg_clima` | `raw_clima` | **UNNEST 2:** cinco `unnest` lado a lado → uma linha por hora |
| `raw_feriados` | `data/raw/nager/*.json` | `payload` é um array de feriados |
| `stg_feriados` | `raw_feriados` | **UNNEST 3:** uma linha por feriado |
| `stg_feriados_uf` | `stg_feriados` | **UNNEST 4:** `LEFT JOIN LATERAL (SELECT unnest(counties))` → uma linha por UF, preservando o feriado nacional |

## 3. SQL — `sql/02_transform.sql`

| Etapa | Tabelas | O que faz |
|---|---|---|
| **T1** Tipos e datas | `t1_ons`, `t1_clima`, `t1_feriados` | `TRY_CAST` para `DATE` e `TIMESTAMP`; remove o `Z` (o instante já é UTC); códigos em maiúsculas; `BR-SP` → `SP`; mantém só feriado `Public` |
| **T2** Nulos | `rejeitados_ons`, `t2_ons`, `t2_clima` | Separa os registros do ONS com área, data, instante ou carga nulos, com o motivo; mantém o clima nulo |
| **T3** Deduplicação | `t3_ons`, `t3_clima`, `t3_feriados` | `ROW_NUMBER` por chave; no ONS vence o `din_atualizacao` mais recente; feriados agregados por (data, UF) |
| Agregação | `carga_horaria` | `date_trunc('hour', instante − 30 min)`; média, máximo, média da MMGD, contagem de intervalos |
| **T4** JOIN | `t4_cruzado` | `carga_horaria` ⋈ `dim_areas` (interno) ⟕ `t3_clima` (área, hora) ⟕ `t3_feriados` (data de referência, UF) |
| **T5** Métricas | `carga_clima_horaria` | Participação da MMGD, variação D-1 (auto-junção com a hora − 24 h), dia da semana, fim de semana, ano, mês |

## 4. Como acrescentar uma etapa
1. Criar a tabela nova em `sql/02_transform.sql`, lendo da etapa anterior.
2. Se a contagem interessar ao relatório, incluir em `STAGE_TABLES` (`transform.py`).
3. Se mudar o dataset final, atualizar `CONTRACT` (`quality.py`).
4. Escrever o teste em `tests/test_transform.py` com entrada e saída conhecidas.
5. Atualizar `regras-de-negocio.md` e `dicionario-de-dados.md`.
