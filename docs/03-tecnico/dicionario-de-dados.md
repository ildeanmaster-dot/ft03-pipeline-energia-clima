# Dicionário de dados

Versão 1.0 · 12/11/2026

Classe: **Origem** = veio da API sem cálculo; **Cálculo** = fórmula rastreável;
**Parâmetro** = `config/areas_carga.csv`. Não há coluna inferida.

## 1. Dataset final — `carga_clima_horaria`

Local: `output/dataset/ano=AAAA/mes=M/*.parquet` · Granularidade: área de carga × hora UTC ·
Chave: (`cod_areacarga`, `hora_utc`).

| # | Coluna | Tipo | Nulo? | Classe | Fonte ou fórmula | Unidade |
|---|---|---|---|---|---|---|
| 1 | `cod_areacarga` | VARCHAR | Não | Origem | ONS `cod_areacarga`, em maiúsculas | — |
| 2 | `nome_area` | VARCHAR | Não | Parâmetro | `areas_carga.csv` | — |
| 3 | `uf` | VARCHAR | Não | Parâmetro | `areas_carga.csv` | — |
| 4 | `dat_referencia` | DATE | Não | Origem | ONS `dat_referencia` | — |
| 5 | `hora_utc` | TIMESTAMP | Não | Cálculo | `date_trunc('hour', din_referenciautc − 30 min)` | UTC |
| 6 | `carga_media_mw` | DOUBLE | Não | Cálculo | Média de `val_cargaglobal` dos intervalos da hora | MWmed |
| 7 | `carga_max_mw` | DOUBLE | Não | Cálculo | Máximo de `val_cargaglobal` na hora | MWmed |
| 8 | `carga_mmgd_media_mw` | DOUBLE | Até 5% | Cálculo | Média de `val_cargammgd` na hora | MWmed |
| 9 | `qtd_intervalos` | INTEGER | Não | Cálculo | Intervalos de 30 min presentes na hora (1 ou 2) | — |
| 10 | `temperatura_c` | DOUBLE | Até 5% | Origem | Open-Meteo `temperature_2m` | °C |
| 11 | `umidade_relativa_pct` | DOUBLE | Até 5% | Origem | Open-Meteo `relative_humidity_2m` | % |
| 12 | `sensacao_termica_c` | DOUBLE | Até 5% | Origem | Open-Meteo `apparent_temperature` | °C |
| 13 | `precipitacao_mm` | DOUBLE | Até 5% | Origem | Open-Meteo `precipitation` | mm |
| 14 | `clima_disponivel` | BOOLEAN | Não | Cálculo | Existe clima para (área, hora) e a temperatura não é nula | — |
| 15 | `eh_feriado` | BOOLEAN | Não | Cálculo | Existe feriado público para (`dat_referencia`, `uf`) | — |
| 16 | `nome_feriado` | VARCHAR | Sim | Origem | Nager.Date `localName`; nomes unidos por " / " se houver mais de um | — |
| 17 | `dia_semana` | INTEGER | Não | Cálculo | `isodow(dat_referencia)`: 1 = segunda … 7 = domingo | — |
| 18 | `eh_fim_de_semana` | BOOLEAN | Não | Cálculo | `dia_semana` é 6 ou 7 | — |
| 19 | `participacao_mmgd_pct` | DOUBLE | Até 5% | Cálculo | `100 × carga_mmgd_media_mw ÷ carga_media_mw`; nulo se a carga for zero | % |
| 20 | `variacao_carga_d1_pct` | DOUBLE | Sim | Cálculo | `100 × (carga − carga 24 h antes) ÷ carga 24 h antes`; nulo sem o dia anterior | % |
| 21 | `din_atualizacao_ons` | TIMESTAMP | Sim | Origem | Maior `din_atualizacao` dos registros da hora | UTC |
| 22 | `ano` | INTEGER | Não | Cálculo | `year(dat_referencia)`; fica no nome da pasta | — |
| 23 | `mes` | INTEGER | Não | Cálculo | `month(dat_referencia)`; fica no nome da pasta | — |

Observações:
- `ano` e `mes` não ficam dentro do arquivo Parquet. Leia com `hive_partitioning = true`.
- `hora_utc` é o **início** da hora. A temperatura é o valor naquele instante; a carga é a média da hora.
- O primeiro dia do período tem `variacao_carga_d1_pct` nulo em todas as horas.
- `dat_referencia` é a data do ONS (dia de Brasília), não a data de `hora_utc`: as horas de
  00:00 a 02:00 UTC pertencem à data de referência do dia anterior.

## 2. Tabela de rejeitados — `rejeitados_ons` (só em memória)
Colunas de `t1_ons` mais `motivo_rejeicao`: `area_nula`, `data_referencia_invalida`,
`instante_invalido` ou `carga_global_nula`. A contagem vai para o relatório em
`linhas_por_etapa.ons_rejeitados_por_nulo`.

## 3. Parâmetro — `dim_areas`
`cod_areacarga`, `nome_area`, `uf`, `latitude`, `longitude`. Origem e fontes em
`docs/03-tecnico/fontes-de-dados.md`, seção 4.

## 4. Tabelas intermediárias (em memória)
| Tabela | Uma linha é | Colunas principais |
|---|---|---|
| `stg_ons` | Um registro semi-horário, como veio | Os 11 campos do ONS, em texto e número, mais `arquivo_origem` |
| `t3_ons` | Um registro semi-horário válido e único | `cod_areacarga`, `dat_referencia`, `din_referencia_utc`, `din_atualizacao_utc`, `val_cargaglobal`, `val_cargammgd` |
| `carga_horaria` | Uma área numa hora | `hora_utc`, `carga_media_mw`, `carga_max_mw`, `carga_mmgd_media_mw`, `qtd_intervalos` |
| `stg_clima` | Uma área numa hora, como veio | `time_txt` e as quatro variáveis, mais a coordenada da grade |
| `t3_clima` | Uma área numa hora, única | `hora_utc`, `temperatura_c`, `umidade_relativa_pct`, `sensacao_termica_c`, `precipitacao_mm` |
| `stg_feriados_uf` | Um feriado numa UF (ou nacional, com `county` nulo) | `date_txt`, `nome_local`, `nacional`, `tipos`, `county` |
| `t3_feriados` | Uma data numa UF | `data_feriado`, `uf`, `nome_feriado`, `feriado_nacional` |
| `t4_cruzado` | Uma área numa hora, com clima e feriado | Colunas finais antes das métricas |

## 5. Relatório — `output/reports/quality_report.json`
| Campo | Conteúdo |
|---|---|
| `run_id` | Identificador da execução |
| `status` | `success`, `success_with_warnings`, `failed_quality` ou `failed` |
| `inicio_utc`, `fim_utc`, `duracao_s` | Tempo da execução |
| `periodo`, `areas` | O que foi pedido |
| `extracao` | Por fonte: `requisicoes`, `retentativas`, `bytes_recebidos`, `espera_rate_limit_s`, `arquivos_brutos`, `registros`, `avisos` |
| `linhas_por_etapa` | Contagem de 14 tabelas, da leitura ao resultado final |
| `null_ratio_por_coluna` | Fração de nulos de cada coluna do dataset final |
| `verificacoes` | Lista com `check`, `dimension`, `severity`, `passed`, `observed`, `expected`, `detail` |
| `resumo_verificacoes` | `total`, `aprovadas`, `falhas_bloqueantes`, `avisos` |
| `particoes_gravadas` | `ano`, `mes`, `linhas`, `arquivos` |
| `dataset` | `linhas_no_dataset` e `compressao`, relidos do disco |
| `erros` | Mensagens de falha |
