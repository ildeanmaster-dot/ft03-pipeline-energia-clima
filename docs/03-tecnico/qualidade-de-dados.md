# Qualidade de dados

Versão 1.0 · 12/11/2026

## 1. Onde a qualidade é controlada
| Momento | Controle | Onde |
|---|---|---|
| Extração | Campos obrigatórios do ONS; cobertura de dias; 48 registros por dia; arrays do Open-Meteo com o mesmo tamanho e o total de horas; feriado com `date` | `extract.py` |
| Leitura | Schema declarado no `read_json` e no `read_csv`: tipo inesperado falha | `sql/01_staging.sql` |
| Transformação | Rejeição com motivo; deduplicação; contagem de linhas por etapa | `sql/02_transform.sql`, `transform.py` |
| Saída | Contrato e verificações | `quality.py` |
| Gravação | Releitura do Parquet: linhas e compressão | `persist.py` |

## 2. Verificações sobre o dataset final (42 por execução)
| Verificação | Dimensão | Severidade | Regra | Esperado |
|---|---|---|---|---|
| `schema_contrato` | schema | erro | Nomes e tipos iguais a `CONTRACT` | 23 colunas |
| `null_ratio:<coluna>` (23) | nulos | erro se o limite é 0; aviso nos demais | Fração de nulos ≤ limite da coluna | 0 nas obrigatórias; ≤ 0,05 em clima, MMGD e participação; livre em `nome_feriado`, `variacao_carga_d1_pct`, `din_atualizacao_ons` |
| `unicidade_chave` | unicidade | erro | Chaves (`cod_areacarga`, `hora_utc`) repetidas | 0 |
| `intervalo:<coluna>` (12) | intervalo | ver tabela abaixo | Valores não nulos fora do intervalo | 0 |
| `volume_nao_vazio` | volume | erro | Linhas no resultado | > 0 |
| `join_sem_multiplicacao` | join | erro | Linhas finais = horas de carga das áreas do parâmetro | Igual |
| `join_cobertura_clima` | join | aviso | Fração das horas com clima | ≥ 0,95 |
| `areas_solicitadas_presentes` | completude | aviso | Áreas pedidas que aparecem no resultado | Todas |
| `dias_com_24_horas_completas` | completude | aviso | Pares (área, dia) sem 24 horas ou com hora de 1 intervalo | 0 |

### Intervalos
| Coluna | Mínimo | Máximo | Severidade | Justificativa |
|---|---|---|---|---|
| `temperatura_c` | −20 | 55 | erro | Faixa fisicamente plausível (regra do projeto) |
| `sensacao_termica_c` | −30 | 65 | erro | Idem |
| `umidade_relativa_pct` | 0 | 100 | erro | Definição de percentual |
| `precipitacao_mm` | 0 | 500 | erro | Faixa plausível por hora (regra do projeto) |
| `carga_mmgd_media_mw` | 0 | 100.000 | erro | O dicionário do ONS não admite MMGD negativa |
| `qtd_intervalos` | 1 | 2 | erro | Uma hora tem no máximo dois intervalos de 30 min |
| `dia_semana` | 1 | 7 | erro | Padrão ISO |
| `ano` | 2016 | 2100 | erro | Histórico do ONS começa em 2016 |
| `mes` | 1 | 12 | erro | Calendário |
| `carga_media_mw`, `carga_max_mw` | 0 | 100.000 | aviso | O dicionário do ONS admite valor negativo |
| `participacao_mmgd_pct` | 0 | 100 | aviso | Depende da carga, que pode ser negativa |

Os limites de clima e carga são **provisórios**: revisar com os valores observados na
primeira execução real (RN-35, RN-37, RN-38, RN-40).

## 3. Política
- **Erro que falha:** o Parquet não é gravado; o que já estava em `output/dataset/` fica como
  estava; `status = failed_quality`; código de saída 1.
- **Aviso que falha:** o Parquet é gravado; `status = success_with_warnings`; código de saída 0.
- **Schema fora do contrato:** as verificações que dependem de nome e tipo não são executadas;
  a falha de schema já bloqueia.
- **Relatório:** gravado em todos os casos, inclusive em erro de extração.

## 4. Como ler o relatório
1. `status` e `erros`: a execução terminou? Por quê não?
2. `resumo_verificacoes`: `falhas_bloqueantes` tem de ser 0.
3. `verificacoes` com `passed: false`: ler `observed`, `expected` e `detail`.
4. `extracao.<fonte>.avisos`: dias sem dado, dias sem 48 registros.
5. `extracao.<fonte>.retentativas`: se alto, a API estava instável.
6. `linhas_por_etapa`: a queda entre etapas tem de ser explicável:
   - `ons_registros_apos_unnest` − `ons_rejeitados_por_nulo` = `ons_apos_tratamento_nulos`;
   - `ons_apos_tratamento_nulos` − duplicatas = `ons_apos_deduplicacao`;
   - `ons_horas_agregadas` ≈ `ons_apos_deduplicacao` ÷ 2;
   - `apos_join` = `final` = `ons_horas_agregadas` (das áreas do parâmetro).
7. `dataset.linhas_no_dataset` = `linhas_por_etapa.final` quando todas as partições são da execução.

## 5. Valores de referência (período padrão, 20 áreas, sem lacunas)
| Campo | Valor esperado | Conta |
|---|---|---|
| `ons_registros_apos_unnest` | 88.320 | 20 × 92 × 48 |
| `clima_horas_apos_unnest` | 44.640 | 20 × 93 × 24 |
| `ons_horas_agregadas` e `final` | 44.160 | 20 × 92 × 24 |
| `feriados_apos_unnest` | 15 | Feriados de 2026 na chamada de 12/11/2026 |
| Partições | 3 | `mes=8` (14.880), `mes=9` (14.400), `mes=10` (14.880) |

Diferença em relação a esses valores não é necessariamente erro: confira os avisos da extração.
