# Fontes de dados

Versão 1.1 · 23/11/2026

Tudo aqui foi conferido em 12/11/2026 na documentação indicada ou em chamada real. O que não
está publicado aparece como "não publicado"; o que não foi conferido, como **[a validar]**.

## 1. ONS — Carga Verificada

| Item | Valor | Fonte |
|---|---|---|
| Endpoint | `GET https://apicarga.ons.org.br/prd/cargaverificada` | Portal de dados abertos do ONS |
| Parâmetros | `dat_inicio`, `dat_fim` (AAAA-MM-DD), `cod_areacarga` | Portal |
| Documentação | http://ons-dl-prod-opendata-swagger.s3-website-us-east-1.amazonaws.com | Portal |
| Dicionário | https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/carga_verificada_tm/DicionarioDados_Carga_Verificada.pdf | Portal |
| Autenticação | Nenhuma | Chamada real |
| Licença | Creative Commons Attribution | Portal |
| Limite de taxa | Não publicado; resposta sem cabeçalho de limite | Swagger e chamada real |
| Histórico | Desde 01/01/2016 | Swagger |
| Periodicidade | Semi-horária: 48 registros por dia e área | Portal e chamada real |
| Unidade | MWmed, valor integralizado no fim do intervalo | Swagger e dicionário |
| Fuso | `din_referenciautc` em UTC | Swagger |
| Formato | Array JSON de objetos planos | Chamada real |

**Campos do registro**

| Campo | Tipo na resposta | Descrição (dicionário/Swagger) | Usado |
|---|---|---|---|
| `cod_areacarga` | texto | Código da área de carga | Sim |
| `din_atualizacao` | texto ISO com `Z` | Instante de atualização (não consta no dicionário; presente na resposta) | Sim (deduplicação) |
| `dat_referencia` | texto AAAA-MM-DD | Data de referência | Sim |
| `din_referenciautc` | texto ISO com `Z` | Fim do intervalo semi-horário, em UTC | Sim |
| `val_cargaglobal` | número | Carga global | Sim |
| `val_cargammgd` | número | Carga atendida por micro e minigeração distribuída | Sim |
| `val_cargaglobalcons` | número | Carga global consistida para os modelos de previsão | Lido, não usado |
| `val_cargaglobalsmmgd` | número | Carga global líquida de MMGD | Lido, não usado |
| `val_cargasupervisionada` | número | Parcela supervisionada pelo ONS | Lido, não usado |
| `val_carganaosupervisionada` | número | Parcela da medição de faturamento da CCEE | Lido, não usado |
| `val_consistencia` | número | Parcela de consistência para os modelos de previsão | Lido, não usado |

O dicionário admite valor zerado e negativo em `val_cargaglobal`.

**Códigos de área.** O Swagger lista 33: SECO, S, NE, N, RJ, SP, MG, ES, MT, MS, DF, GO, AC, RO,
PR, SC, RS, BASE, BAOE, ALPE, PBRN, CE, PI, TON, PA, MA, AP, AM, RR, PESE, PES, PENE, PEN.
O dicionário os agrupa em submercado, área geoelétrica e perdas, e dá o nome de cada um.
O projeto usa as 20 áreas geoelétricas de nome igual a uma UF (ver seção 4).

**Comportamentos confirmados**
- **Resposta cortada em silêncio.** PA, 01/06 a 30/09/2026: HTTP 200, JSON válido, 2,48 MB,
  107 de 122 dias. PA, 01/01 a 30/09/2026: 106 dias, 2,46 MB. Um mês: 1.488 registros, 0,72 MB, completo.
- **Dia de referência.** `dat_referencia = 2026-10-01` cobre de `2026-10-01T03:30Z` a `2026-10-02T03:00Z`.
- **Qualidade observada.** Outubro/2026 em 10 áreas: 48 registros em todos os dias, sem nulos,
  sem negativos, sem chaves repetidas.
- **JSON inválido quando falta valor:** relato de terceiros, não reproduzido **[a validar]**;
  se acontecer, a extração para com `ExtractionError` (nada é reparado).
- **`precipitation`:** soma da hora anterior (*preceding hour sum*); as outras 3 variáveis são
  instantâneas (documentação do Open-Meteo, consultada em 23/11/2026).

Outro endpoint da mesma API, não usado: `/cargaprogramada` (desde 05/03/2021, segundo o Swagger).

## 2. Open-Meteo — Historical Weather

| Item | Valor | Fonte |
|---|---|---|
| Endpoint | `GET https://archive-api.open-meteo.com/v1/archive` | https://open-meteo.com/en/docs/historical-weather-api |
| Parâmetros usados | `latitude`, `longitude`, `start_date`, `end_date`, `hourly`, `timezone=UTC` | Documentação |
| Autenticação | Nenhuma no plano gratuito | https://open-meteo.com/en/terms |
| Limite de taxa | 600/min, 5.000/h, 10.000/dia, 300.000/mês | Termos |
| Licença | CC BY 4.0; plano gratuito só para uso não comercial | Termos |
| Dados desde | 1940 | Documentação |
| Erro de parâmetro | HTTP 400 com `{"reason": "...", "error": true}` | Chamada real |
| Endpoint comercial | `customer-archive-api.open-meteo.com` com `apikey` | **[a validar]**: não foi testado; usado só se `OPEN_METEO_API_KEY` estiver definida |

**Formato da resposta**

```json
{
  "latitude": -3.9718807, "longitude": -53.06189, "elevation": 171.0, "timezone": "GMT",
  "hourly_units": {"time": "iso8601", "temperature_2m": "°C", "relative_humidity_2m": "%",
                   "apparent_temperature": "°C", "precipitation": "mm"},
  "hourly": {
    "time": ["2026-10-11T00:00", "2026-10-11T01:00"],
    "temperature_2m": [28.1, 27.7],
    "relative_humidity_2m": [63, 66],
    "apparent_temperature": [30.4, 30.5],
    "precipitation": [0.0, 0.0]
  }
}
```

`hourly` são arrays paralelos: a posição `i` de cada array pertence a `time[i]`.

**Comportamentos confirmados**
- A coordenada devolvida é a do ponto de grade (−3,9812 / −53,072 pedida → −3,9718807 / −53,06189).
- Com várias coordenadas numa chamada, a resposta vira lista e o primeiro elemento vem sem
  `location_id`. O projeto faz uma chamada por área.
- Centróide do PA, 01/08 a 31/10/2026: 2.208 horas, nenhuma variável com nulo.

## 3. Nager.Date — Public Holidays

| Item | Valor | Fonte |
|---|---|---|
| Endpoint | `GET https://date.nager.at/api/v3/PublicHolidays/{ano}/BR` | https://date.nager.at/API |
| Autenticação | Nenhuma | Chamada real |
| Limite de taxa | Não publicado | — |
| Natureza | Projeto de código aberto mantido pela comunidade | Repositório do projeto |
| Resposta 2026 | 15 feriados | Chamada real |

**Campos:** `date`, `localName`, `name`, `countryCode`, `fixed`, `global`, `counties`,
`launchYear`, `types`.

- `global = true` e `counties = null`: feriado nacional.
- `global = false` e `counties = ["BR-SP"]`: feriado da UF indicada (ex.: 09/07/2026,
  Revolução Constitucionalista de 1932).
- `types` é uma lista; o projeto usa só os que contêm `Public`.

## 4. Parâmetro — `config/areas_carga.csv`

Não é uma API consumida pelo pipeline: é um arquivo versionado, montado uma vez, com a fonte
em cada linha.

| Coluna | Conteúdo | Fonte |
|---|---|---|
| `cod_areacarga` | Código da área no ONS | Swagger e dicionário do ONS |
| `nome_area` | Nome da área geoelétrica | Dicionário do ONS |
| `uf` | Sigla da UF de mesmo nome | Dicionário do ONS (nome) |
| `codigo_ibge_uf` | Código da UF | Campo `id` da API de Malhas do IBGE |
| `latitude`, `longitude` | Centróide da UF | `GET https://servicodados.ibge.gov.br/api/v4/malhas/estados/{UF}/metadados`, campo `centroide`, em 12/11/2026 |
| `fonte_nome_area`, `fonte_coordenada` | Texto com a origem de cada dado | — |

**Áreas incluídas (20):** AC, AM, AP, CE, DF, ES, GO, MA, MG, MS, MT, PA, PI, PR, RJ, RO, RR, RS, SC, SP.

**Fora:** submercados (SECO, S, NE, N); áreas de mais de uma UF ou de parte de uma UF
(BASE, BAOE, ALPE, PBRN, TON); perdas (PEN, PES, PENE, PESE).

**Limitação:** a relação "área geoelétrica = UF" vem só do nome dado pelo dicionário; o limite
elétrico pode não coincidir com o limite do estado.

## 5. Onde a camada bruta fica
| Fonte | Arquivo | `meta` |
|---|---|---|
| ONS | `data/raw/ons/{AREA}_{inicio}_{fim}.json` | `cod_areacarga`, `dat_inicio`, `dat_fim`, `extraido_em` |
| Open-Meteo | `data/raw/open_meteo/{AREA}_{inicio}_{fim}.json` | idem + `latitude_solicitada`, `longitude_solicitada` |
| Nager.Date | `data/raw/nager/BR_{ano}.json` | `ano`, `pais`, `extraido_em` |
