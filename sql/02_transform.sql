-- =====================================================================
-- 02_transform.sql — as 5 transformações obrigatórias, identificadas T1..T5
-- Saída: tabela carga_clima_horaria (1 linha = área de carga x hora UTC)
-- =====================================================================

-- ---------------------------------------------------------------------
-- T1 — PADRONIZAÇÃO DE TIPOS E DATAS
-- Textos ISO viram DATE/TIMESTAMP (UTC, sem fuso); códigos em maiúsculas.
-- TRY_CAST devolve NULL em valor inválido, que é tratado em T2.
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE t1_ons AS
SELECT
    upper(trim(cod_areacarga))                                   AS cod_areacarga,
    try_cast(dat_referencia AS DATE)                             AS dat_referencia,
    try_cast(replace(din_referenciautc, 'Z', '') AS TIMESTAMP)   AS din_referencia_utc,
    try_cast(replace(din_atualizacao, 'Z', '') AS TIMESTAMP)     AS din_atualizacao_utc,
    val_cargaglobal,
    val_cargammgd,
    arquivo_origem
FROM stg_ons;

CREATE OR REPLACE TABLE t1_clima AS
SELECT
    upper(trim(cod_areacarga))          AS cod_areacarga,
    try_cast(time_txt AS TIMESTAMP)     AS hora_utc,
    temperature_2m                      AS temperatura_c,
    relative_humidity_2m                AS umidade_relativa_pct,
    apparent_temperature                AS sensacao_termica_c,
    precipitation                       AS precipitacao_mm,
    extraido_em,
    arquivo_origem
FROM stg_clima;

CREATE OR REPLACE TABLE t1_feriados AS
SELECT
    try_cast(date_txt AS DATE)                AS data_feriado,
    nome_local,
    coalesce(nacional, false)                 AS nacional,
    upper(replace(county, 'BR-', ''))         AS uf
FROM stg_feriados_uf
WHERE list_contains(tipos, 'Public');

-- ---------------------------------------------------------------------
-- T2 — TRATAMENTO DE NULOS
-- Regra: chave ou medida principal nula -> registro REJEITADO e contado
-- (não é preenchido por suposição). Medida de clima nula é PRESERVADA
-- como NULL (dado não disponível na origem) e sinalizada no resultado.
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE rejeitados_ons AS
SELECT
    *,
    CASE
        WHEN cod_areacarga IS NULL OR cod_areacarga = '' THEN 'area_nula'
        WHEN dat_referencia IS NULL THEN 'data_referencia_invalida'
        WHEN din_referencia_utc IS NULL THEN 'instante_invalido'
        WHEN val_cargaglobal IS NULL THEN 'carga_global_nula'
    END AS motivo_rejeicao
FROM t1_ons
WHERE cod_areacarga IS NULL OR cod_areacarga = ''
   OR dat_referencia IS NULL
   OR din_referencia_utc IS NULL
   OR val_cargaglobal IS NULL;

CREATE OR REPLACE TABLE t2_ons AS
SELECT *
FROM t1_ons
WHERE cod_areacarga IS NOT NULL AND cod_areacarga <> ''
  AND dat_referencia IS NOT NULL
  AND din_referencia_utc IS NOT NULL
  AND val_cargaglobal IS NOT NULL;

CREATE OR REPLACE TABLE t2_clima AS
SELECT * FROM t1_clima
WHERE cod_areacarga IS NOT NULL AND hora_utc IS NOT NULL;

-- ---------------------------------------------------------------------
-- T3 — DEDUPLICAÇÃO
-- ONS: chave (área, instante); vence o registro com din_atualizacao mais
-- recente. Clima: chave (área, hora); vence a extração mais recente (o
-- desempate nunca usa o valor medido). Feriados: um por (data, UF).
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE t3_ons AS
SELECT *
FROM t2_ons
QUALIFY row_number() OVER (
    PARTITION BY cod_areacarga, din_referencia_utc
    ORDER BY din_atualizacao_utc DESC NULLS LAST, arquivo_origem DESC
) = 1;

CREATE OR REPLACE TABLE t3_clima AS
SELECT *
FROM t2_clima
QUALIFY row_number() OVER (
    PARTITION BY cod_areacarga, hora_utc
    ORDER BY extraido_em DESC NULLS LAST, arquivo_origem DESC
) = 1;

-- Feriado nacional vale para todas as UFs do parâmetro; regional só para a
-- sua. Dois feriados no mesmo dia/UF viram UMA linha (evita multiplicar o JOIN).
CREATE OR REPLACE TABLE t3_feriados AS
WITH por_uf AS (
    SELECT f.data_feriado, a.uf, f.nome_local, f.nacional
    FROM t1_feriados AS f
    JOIN (SELECT DISTINCT uf FROM dim_areas) AS a
      ON f.nacional OR f.uf = a.uf
    WHERE f.data_feriado IS NOT NULL
)
SELECT
    data_feriado,
    uf,
    string_agg(DISTINCT nome_local, ' / ' ORDER BY nome_local) AS nome_feriado,
    bool_or(nacional)                                          AS feriado_nacional
FROM por_uf
GROUP BY data_feriado, uf;

-- Granularidade final: hora cheia. O ONS integra o valor no FIM do intervalo
-- semi-horário, então os instantes HH:30 e (HH+1):00 formam a hora HH:00.
CREATE OR REPLACE TABLE carga_horaria AS
SELECT
    cod_areacarga,
    dat_referencia,
    date_trunc('hour', din_referencia_utc - INTERVAL 30 MINUTE)  AS hora_utc,
    avg(val_cargaglobal)                                         AS carga_media_mw,
    max(val_cargaglobal)                                         AS carga_max_mw,
    avg(val_cargammgd)                                           AS carga_mmgd_media_mw,
    count(*)::INTEGER                                            AS qtd_intervalos,
    max(din_atualizacao_utc)                                     AS din_atualizacao_ons
FROM t3_ons
GROUP BY ALL;

-- ---------------------------------------------------------------------
-- T4 — CRUZAMENTO DE FONTES (JOIN)
-- carga (ONS) x parâmetro de áreas x clima (Open-Meteo) x feriados (Nager).
-- Chaves: clima = (área, hora UTC); feriado = (data de referência, UF).
-- LEFT JOIN: hora sem clima ou sem feriado continua no resultado.
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE t4_cruzado AS
SELECT
    c.cod_areacarga,
    a.nome_area,
    a.uf,
    c.dat_referencia,
    c.hora_utc,
    c.carga_media_mw,
    c.carga_max_mw,
    c.carga_mmgd_media_mw,
    c.qtd_intervalos,
    w.temperatura_c,
    w.umidade_relativa_pct,
    w.sensacao_termica_c,
    w.precipitacao_mm,
    (w.cod_areacarga IS NOT NULL AND w.temperatura_c IS NOT NULL)  AS clima_disponivel,
    (f.data_feriado IS NOT NULL)                                   AS eh_feriado,
    f.nome_feriado,
    c.din_atualizacao_ons
FROM carga_horaria AS c
JOIN dim_areas AS a
  ON a.cod_areacarga = c.cod_areacarga
LEFT JOIN t3_clima AS w
  ON w.cod_areacarga = c.cod_areacarga AND w.hora_utc = c.hora_utc
LEFT JOIN t3_feriados AS f
  ON f.data_feriado = c.dat_referencia AND f.uf = a.uf;

-- ---------------------------------------------------------------------
-- T5 — ENRIQUECIMENTO COM MÉTRICAS DERIVADAS
--   participacao_mmgd_pct  = 100 * carga MMGD / carga global
--   variacao_carga_d1_pct  = variação % contra a mesma hora do dia anterior
--   dia_semana / eh_fim_de_semana = calendário da data de referência
-- Divisão por zero e dia anterior ausente resultam em NULL (não em 0).
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE carga_clima_horaria AS
SELECT
    t.cod_areacarga,
    t.nome_area,
    t.uf,
    t.dat_referencia,
    t.hora_utc,
    t.carga_media_mw,
    t.carga_max_mw,
    t.carga_mmgd_media_mw,
    t.qtd_intervalos,
    t.temperatura_c,
    t.umidade_relativa_pct,
    t.sensacao_termica_c,
    t.precipitacao_mm,
    t.clima_disponivel,
    t.eh_feriado,
    t.nome_feriado,
    isodow(t.dat_referencia)::INTEGER                                       AS dia_semana,
    (isodow(t.dat_referencia) IN (6, 7))                                    AS eh_fim_de_semana,
    100.0 * t.carga_mmgd_media_mw / nullif(t.carga_media_mw, 0)             AS participacao_mmgd_pct,
    100.0 * (t.carga_media_mw - d1.carga_media_mw) / nullif(d1.carga_media_mw, 0)
                                                                            AS variacao_carga_d1_pct,
    t.din_atualizacao_ons,
    year(t.dat_referencia)::INTEGER                                         AS ano,
    month(t.dat_referencia)::INTEGER                                        AS mes
FROM t4_cruzado AS t
LEFT JOIN carga_horaria AS d1
  ON d1.cod_areacarga = t.cod_areacarga
 AND d1.hora_utc = t.hora_utc - INTERVAL 24 HOUR;
