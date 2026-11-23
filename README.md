# Carga de energia × clima × feriados — Desafio Python FT03 (Projeto 1)

Pipeline em Python + SQL (DuckDB) que extrai dados de três APIs públicas, desaninha e
transforma em SQL, valida a qualidade e grava um dataset Parquet (Snappy) particionado
por ano/mês, com relatório de qualidade em JSON.

**Pergunta respondida:** como temperatura e umidade se relacionam com a carga de energia
elétrica, por área de carga e por hora, e se feriados alteram esse padrão.

## 1. Fontes de dados

| | API | Domínio | Provedor | Autenticação | Limite de taxa |
|---|---|---|---|---|---|
| A | [Carga Verificada](https://dados.ons.org.br/dataset/carga-energia-verificada) | Energia elétrica | ONS | Nenhuma | Não publicado |
| B | [Historical Weather](https://open-meteo.com/en/docs/historical-weather-api) | Clima | Open-Meteo | Nenhuma (plano gratuito) | 600/min, 5.000/h, 10.000/dia |
| C | [Public Holidays v3](https://date.nager.at/API) | Calendário | Nager.Date | Nenhuma | Não publicado |

Fatos conferidos em 12/11/2026 na documentação e em chamadas reais:

- **ONS** — `GET https://apicarga.ons.org.br/prd/cargaverificada?dat_inicio=&dat_fim=&cod_areacarga=`
  ([Swagger](http://ons-dl-prod-opendata-swagger.s3-website-us-east-1.amazonaws.com)).
  Devolve um array com 48 registros por dia (intervalos de 30 min), em MWmed, com o valor
  integralizado no **fim** do intervalo e o instante em UTC. Licença CC-BY.
  **Atenção:** em períodos longos a API responde HTTP 200 com a lista **cortada**, sem erro
  (área PA, 01/06 a 30/09/2026: vieram 107 de 122 dias). O pipeline pede um mês por vez,
  confere os dias recebidos e divide a janela quando falta algum.
- **Open-Meteo** — `GET https://archive-api.open-meteo.com/v1/archive`. O objeto `hourly`
  traz arrays paralelos (`time[]` e um array por variável). Uso gratuito apenas não
  comercial, licença CC BY 4.0. A coordenada devolvida é a do ponto de grade mais próximo,
  por isso a área é identificada pelo que foi pedido, e não pela coordenada da resposta.
- **Nager.Date** — `GET https://date.nager.at/api/v3/PublicHolidays/{ano}/BR`. Cada feriado
  tem os arrays `types[]` e `counties[]` (UF no formato `BR-SP`; `null` em feriado nacional).

### Parâmetro: áreas de carga e coordenadas

Nenhuma API liga área de carga a latitude/longitude. Esse vínculo está em
[`config/areas_carga.csv`](config/areas_carga.csv), com a fonte em cada linha:

- **Áreas:** as 20 "áreas geoelétricas" que o
  [dicionário de dados do ONS](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/carga_verificada_tm/DicionarioDados_Carga_Verificada.pdf)
  nomeia com uma única UF (AC, AM, AP, CE, DF, ES, GO, MA, MG, MS, MT, PA, PI, PR, RJ, RO,
  RR, RS, SC, SP). Submercados, áreas compostas (ex.: ALPE, PBRN) e perdas ficam fora.
- **Coordenada:** centróide da UF, da
  [API de Malhas do IBGE](https://servicodados.ibge.gov.br/api/docs/malhas?versao=4)
  (`/api/v4/malhas/estados/{UF}/metadados`), consultada em 12/11/2026.

## 2. Arquitetura

```
ONS ─────────┐
Open-Meteo ──┼─► data/raw/*.json ─► SQL DuckDB ─► qualidade ─► output/dataset/ano=/mes=/*.parquet
Nager.Date ──┘   (retorno bruto)    UNNEST + T1..T5            output/reports/quality_report.json
```

```
src/pipeline/
  config.py        configuração por variáveis de ambiente
  http_client.py   controle de taxa, retentativas, erros classificados
  extract.py       extração das 3 APIs para a camada bruta
  transform.py     executa os arquivos SQL
  quality.py       contrato de schema e verificações
  persist.py       Parquet Snappy particionado, idempotente
  main.py          orquestração e relatório
sql/
  01_staging.sql   leitura da camada bruta e desaninhamento (UNNEST)
  02_transform.sql transformações T1 a T5
config/areas_carga.csv
scripts/inspecionar_dataset.py   resumo do dataset gravado
tests/             43 testes (pytest), sem depender das APIs ao vivo
docs/              documentação completa (índice em docs/README.md)
.vscode/           tarefas, depuração e testes no VS Code
```

Documentação: [visão não técnica](docs/01-negocio/visao-geral.md) ·
[requisitos e status](docs/01-negocio/requisitos.md) ·
[regras de negócio](docs/01-negocio/regras-de-negocio.md) ·
[arquitetura](docs/02-arquitetura/arquitetura-da-solucao.md) ·
[guia do VS Code](docs/03-tecnico/guia-vscode.md) ·
[índice completo](docs/README.md).

## 3. Como executar

Requisitos: **Python 3.11 ou superior** (exigência do `duckdb` 2.0.0; testado em 3.13) e acesso à internet.

> **Processador sem AVX:** em 12/11/2026 o `duckdb` 2.0.0 encerrou com "Illegal instruction" ao ser
> importado num Linux com processador Intel Core i7-870 (sem AVX). No mesmo ambiente, o `duckdb` 1.5.6
> importou e os 43 testes passaram. Se `python -c "import duckdb"` falhar na sua máquina, troque a linha
> do `requirements.txt` para `duckdb==1.5.6` e reinstale. Detalhes em `docs/00-gestao/debito-tecnico.md` (DT-15).

```bash
git clone <url-do-repositorio>
cd <pasta-do-repositorio>
./run.sh
```

O `run.sh` cria o ambiente virtual, instala o `requirements.txt` e roda o pipeline.
No Windows, use o Git Bash, o script `.\run.ps1` ou, no PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"; .venv\Scripts\python -m pipeline.main
```

Opções: `./run.sh --inicio 2026-10-01 --fim 2026-10-31 --areas PA,SP` ou
`./run.sh --skip-extract` (reaproveita `data/raw` sem chamar as APIs).

Testes: `PYTHONPATH=src .venv/bin/python -m pytest`

### Variáveis de ambiente

Todas são opcionais; copie `.env.example` para `.env` para alterar. O `.env` não é versionado.

| Variável | Padrão | Descrição |
|---|---|---|
| `DATA_INICIO` / `DATA_FIM` | `2026-08-01` / `2026-10-31` | Período (data de referência do ONS) |
| `AREAS` | vazio (todas) | Áreas separadas por vírgula |
| `HTTP_TIMEOUT_CONNECT_S` / `HTTP_TIMEOUT_READ_S` | `10` / `60` | Timeouts |
| `HTTP_MAX_RETRIES` / `HTTP_BACKOFF_FACTOR` | `5` / `1.0` | Retentativas e backoff |
| `ONS_MIN_INTERVAL_S` | `1.0` | Intervalo mínimo entre chamadas ao ONS |
| `OPEN_METEO_MIN_INTERVAL_S` | `0.5` | Idem, Open-Meteo |
| `NAGER_MIN_INTERVAL_S` | `1.0` | Idem, Nager.Date |
| `OPEN_METEO_API_KEY` | vazio | Só para o plano comercial do Open-Meteo |
| `RAW_DIR` / `OUTPUT_DIR` | `data/raw` / `output` | Pastas |

**Credenciais:** as três APIs são abertas e não exigem chave. A única credencial possível
(`OPEN_METEO_API_KEY`, opcional) é lida só do ambiente, nunca aparece em log (as URLs são
mascaradas) e o `.env` está no `.gitignore`.

## 4. Resiliência na extração

- **Controle de taxa:** intervalo mínimo entre chamadas, por API (`RateLimiter`). Para ONS
  e Nager.Date, que não publicam limite, o padrão é conservador (1 chamada por segundo).
- **Retentativas:** `urllib3.Retry` para 429, 500, 502, 503 e 504, timeout e queda de
  conexão; backoff exponencial com jitter; respeita `Retry-After` (até 120 s).
- **Erros permanentes** (400, 401, 403, 404) falham na hora, com mensagem clara.
- **Timeout explícito** de conexão e de leitura em toda chamada.
- **Resposta incompleta do ONS:** detectada pela cobertura de dias e resolvida dividindo a janela.
- **JSON com valor ausente** (`"campo": ,`): reparado para `null` e registrado como aviso.
- **Falha em qualquer etapa:** o relatório é gravado com `status = failed` e o processo sai com código 1.

## 5. Dataset final

Granularidade: **1 linha = 1 área de carga × 1 hora (UTC)**. Chave: (`cod_areacarga`, `hora_utc`).

| Coluna | Tipo | Classe | Descrição |
|---|---|---|---|
| `cod_areacarga` | VARCHAR | Origem (ONS) | Código da área de carga |
| `nome_area`, `uf` | VARCHAR | Parâmetro | Nome e UF da área (`config/areas_carga.csv`) |
| `dat_referencia` | DATE | Origem (ONS) | Data de referência do ONS |
| `hora_utc` | TIMESTAMP | Cálculo | Início da hora cheia, em UTC |
| `carga_media_mw` | DOUBLE | Cálculo | Média de `val_cargaglobal` dos 2 intervalos da hora (MWmed) |
| `carga_max_mw` | DOUBLE | Cálculo | Maior `val_cargaglobal` da hora |
| `carga_mmgd_media_mw` | DOUBLE | Cálculo | Média de `val_cargammgd` (micro e minigeração distribuída) |
| `qtd_intervalos` | INTEGER | Cálculo | Intervalos de 30 min presentes na hora (1 ou 2) |
| `temperatura_c` | DOUBLE | Origem (Open-Meteo) | `temperature_2m` |
| `umidade_relativa_pct` | DOUBLE | Origem (Open-Meteo) | `relative_humidity_2m` |
| `sensacao_termica_c` | DOUBLE | Origem (Open-Meteo) | `apparent_temperature` |
| `precipitacao_mm` | DOUBLE | Origem (Open-Meteo) | `precipitation` |
| `clima_disponivel` | BOOLEAN | Cálculo | Há clima correspondente para a hora |
| `eh_feriado` | BOOLEAN | Cálculo | Feriado público nacional ou da UF na data de referência |
| `nome_feriado` | VARCHAR | Origem (Nager.Date) | Nome local; nulo quando não é feriado |
| `dia_semana` | INTEGER | Cálculo | 1 = segunda … 7 = domingo |
| `eh_fim_de_semana` | BOOLEAN | Cálculo | Sábado ou domingo |
| `participacao_mmgd_pct` | DOUBLE | Cálculo | 100 × `carga_mmgd_media_mw` ÷ `carga_media_mw` |
| `variacao_carga_d1_pct` | DOUBLE | Cálculo | Variação % contra a mesma hora do dia anterior |
| `din_atualizacao_ons` | TIMESTAMP | Origem (ONS) | Atualização mais recente dos registros da hora |
| `ano`, `mes` | INTEGER | Cálculo | Partição, a partir de `dat_referencia` |

**Hora cheia:** o ONS integra o valor no fim do intervalo, então os instantes `HH:30` e
`(HH+1):00` formam a hora `HH:00`. O dia de referência do ONS vai de 03:30 UTC até 03:00 UTC
do dia seguinte; por isso o clima é extraído com um dia a mais.

## 6. Transformações (SQL)

Desaninhamento em [`sql/01_staging.sql`](sql/01_staging.sql):

1. array de registros do ONS → uma linha por registro (`UNNEST(payload, recursive := true)`);
2. arrays paralelos do Open-Meteo → uma linha por hora (vários `UNNEST` lado a lado);
3. array de feriados → uma linha por feriado;
4. `counties[]` → uma linha por UF, com `LEFT JOIN LATERAL` para não perder o feriado
   nacional (no DuckDB, `UNNEST` de lista vazia ou nula gera zero linhas).

Transformações obrigatórias em [`sql/02_transform.sql`](sql/02_transform.sql):

| | Transformação | Regra |
|---|---|---|
| T1 | Tipos e datas | Texto ISO → `DATE`/`TIMESTAMP` em UTC com `TRY_CAST`; códigos em maiúsculas |
| T2 | Nulos | Chave ou carga nula → registro rejeitado e contado. Clima nulo é preservado como nulo e sinalizado. Nada é preenchido por suposição |
| T3 | Deduplicação | ONS por (área, instante), vence o `din_atualizacao` mais recente; clima por (área, hora); feriados por (data, UF) |
| T4 | JOIN | Carga × áreas × clima (área, hora UTC) × feriados (data, UF), com `LEFT JOIN` |
| T5 | Métricas | Participação da MMGD, variação contra D-1, dia da semana, fim de semana |

## 7. Qualidade de dados

Relatório em `output/reports/quality_report.json`: identificação e duração da execução,
requisições e retentativas por API, linhas por etapa, null ratio por coluna, resultado de
cada verificação, partições gravadas e erros.

| Dimensão | Verificação | Severidade |
|---|---|---|
| Schema | Colunas e tipos iguais ao contrato (`quality.py`) | erro |
| Nulos | Null ratio por coluna; 0 nas obrigatórias, até 5% nas de clima | erro / aviso |
| Unicidade | Nenhuma chave (`cod_areacarga`, `hora_utc`) repetida | erro |
| Intervalo | Temperatura −20 a 55 °C, umidade 0 a 100%, precipitação 0 a 500 mm, `qtd_intervalos` 1 a 2, mês 1 a 12 | erro |
| Intervalo | Carga 0 a 100.000 MW; participação MMGD 0 a 100% | aviso |
| JOIN | Linhas finais = horas de carga antes do JOIN (sem multiplicação) | erro |
| JOIN | Pelo menos 95% das horas com clima | aviso |
| Volume | Saída não vazia | erro |
| Completude | Áreas pedidas presentes; 24 horas completas por área e dia | aviso |

**Política:** verificação com severidade *erro* bloqueia a publicação (o Parquet não é
gravado); *aviso* é registrado e não bloqueia. O relatório é gravado nos dois casos.

Os limites de intervalo são regras deste projeto. A carga é só aviso porque o dicionário do
ONS admite valor negativo em `val_cargaglobal`.

## 8. Persistência e reprocessamento

- Parquet com compressão Snappy em `output/dataset/ano=AAAA/mes=M/` (partição Hive pela
  `dat_referencia`). `ano` e `mes` ficam no nome das pastas; leia com
  `read_parquet('output/dataset/**/*.parquet', hive_partitioning = true)`.
- **Idempotência:** as partições do período processado são apagadas e regravadas por
  inteiro; as demais não são tocadas. Rodar duas vezes o mesmo período não duplica dados
  (coberto por teste). Processe meses completos: reprocessar parte de um mês substitui a
  partição inteira pelo que foi extraído.

## 9. Limitações conhecidas

- O centróide da UF não representa onde a carga se concentra; o clima é uma aproximação
  por área. Trocar a coordenada é editar `config/areas_carga.csv`.
- "Área geoelétrica" do ONS não é necessariamente o limite exato da UF.
- `temperature_2m` é o valor no início da hora; a carga é a média da hora.
- Feriados municipais não entram (a API traz nacionais e estaduais).
- ONS e Nager.Date não publicam limite de taxa; o intervalo adotado é uma escolha conservadora.
- Períodos muito recentes podem vir sem clima no arquivo histórico do Open-Meteo; nesse caso as horas ficam com `clima_disponivel = false` e a cobertura aparece como aviso no relatório.
