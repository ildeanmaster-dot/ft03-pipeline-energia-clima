-- =====================================================================
-- 01_staging.sql — leitura da camada bruta e DESANINHAMENTO em SQL (UNNEST)
-- Variáveis definidas pelo Python (SET VARIABLE): raw_ons_glob,
-- raw_clima_glob, raw_feriados_glob, areas_file.
-- O schema de leitura é declarado (contrato de entrada): campo fora do
-- tipo esperado falha aqui, e não mais adiante no pipeline.
-- =====================================================================

-- Parâmetro versionado: área de carga -> UF e coordenada (config/areas_carga.csv)
CREATE OR REPLACE TABLE dim_areas AS
SELECT cod_areacarga, nome_area, uf, latitude, longitude
FROM read_csv(
    getvariable('areas_file'),
    header = true,
    columns = {
        'cod_areacarga': 'VARCHAR', 'nome_area': 'VARCHAR', 'uf': 'VARCHAR',
        'codigo_ibge_uf': 'VARCHAR', 'latitude': 'DOUBLE', 'longitude': 'DOUBLE',
        'fonte_nome_area': 'VARCHAR', 'fonte_coordenada': 'VARCHAR'
    }
);

-- ---------------------------------------------------------------------
-- ONS: cada arquivo traz um ARRAY de registros semi-horários em payload
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE raw_ons AS
SELECT *
FROM read_json(
    getvariable('raw_ons_glob'),
    filename = true,
    columns = {
        'meta': 'STRUCT(cod_areacarga VARCHAR, dat_inicio VARCHAR, dat_fim VARCHAR, extraido_em VARCHAR)',
        'payload': 'STRUCT(
            cod_areacarga VARCHAR, din_atualizacao VARCHAR, dat_referencia VARCHAR,
            din_referenciautc VARCHAR, val_cargaglobal DOUBLE, val_cargaglobalcons DOUBLE,
            val_cargaglobalsmmgd DOUBLE, val_cargasupervisionada DOUBLE,
            val_carganaosupervisionada DOUBLE, val_cargammgd DOUBLE, val_consistencia DOUBLE)[]'
    }
);

-- UNNEST 1: array de structs -> uma linha por registro, um campo por coluna
CREATE OR REPLACE TABLE stg_ons AS
SELECT
    filename AS arquivo_origem,
    unnest(payload, recursive := true)
FROM raw_ons;

-- ---------------------------------------------------------------------
-- Open-Meteo: payload.hourly traz ARRAYS PARALELOS (time[] + um por variável)
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE raw_clima AS
SELECT *
FROM read_json(
    getvariable('raw_clima_glob'),
    filename = true,
    columns = {
        'meta': 'STRUCT(cod_areacarga VARCHAR, latitude_solicitada DOUBLE, longitude_solicitada DOUBLE,
                        dat_inicio VARCHAR, dat_fim VARCHAR, extraido_em VARCHAR)',
        'payload': 'STRUCT(
            latitude DOUBLE, longitude DOUBLE, elevation DOUBLE, timezone VARCHAR,
            hourly STRUCT(
                "time" VARCHAR[], temperature_2m DOUBLE[], relative_humidity_2m DOUBLE[],
                apparent_temperature DOUBLE[], precipitation DOUBLE[]))'
    }
);

-- UNNEST 2: arrays paralelos desaninhados lado a lado -> uma linha por hora
CREATE OR REPLACE TABLE stg_clima AS
SELECT
    meta.cod_areacarga                              AS cod_areacarga,
    payload.latitude                                AS latitude_grade,
    payload.longitude                               AS longitude_grade,
    payload.timezone                                AS fuso_resposta,
    unnest(payload.hourly."time")                   AS time_txt,
    unnest(payload.hourly.temperature_2m)           AS temperature_2m,
    unnest(payload.hourly.relative_humidity_2m)     AS relative_humidity_2m,
    unnest(payload.hourly.apparent_temperature)     AS apparent_temperature,
    unnest(payload.hourly.precipitation)            AS precipitation
FROM raw_clima;

-- ---------------------------------------------------------------------
-- Nager.Date: array de feriados; cada feriado tem os arrays counties[] e types[]
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE raw_feriados AS
SELECT *
FROM read_json(
    getvariable('raw_feriados_glob'),
    columns = {
        'meta': 'STRUCT(ano INTEGER, pais VARCHAR, extraido_em VARCHAR)',
        'payload': 'STRUCT(
            "date" VARCHAR, localName VARCHAR, "name" VARCHAR, countryCode VARCHAR,
            "global" BOOLEAN, counties VARCHAR[], types VARCHAR[])[]'
    }
);

-- UNNEST 3: array de feriados -> uma linha por feriado
CREATE OR REPLACE TABLE stg_feriados AS
SELECT unnest(payload, recursive := true)
FROM raw_feriados;

-- UNNEST 4: counties[] -> uma linha por UF. counties é NULL nos feriados
-- nacionais; UNNEST de lista vazia/NULL gera zero linhas, então o LEFT JOIN
-- LATERAL preserva o feriado nacional (county fica NULL).
CREATE OR REPLACE TABLE stg_feriados_uf AS
SELECT
    f."date"     AS date_txt,
    f.localName  AS nome_local,
    f."global"   AS nacional,
    f.types      AS tipos,
    c.county     AS county
FROM stg_feriados AS f
LEFT JOIN LATERAL (SELECT unnest(f.counties) AS county) AS c ON true;
