# Diagramas

Versão 1.0 · 12/11/2026

Os diagramas estão em Mermaid. No VS Code, instale a extensão recomendada
"Markdown Preview Mermaid Support" e abra a pré-visualização (Ctrl+Shift+V). O GitHub
desenha os blocos automaticamente.

## 1. Contexto

Quem fornece dados ao pipeline e o que ele entrega.

```mermaid
flowchart LR
    ONS["ONS<br/>Carga verificada"]
    OM["Open-Meteo<br/>Clima histórico"]
    NG["Nager.Date<br/>Feriados"]
    IBGE["IBGE Malhas<br/>Centróide da UF"]
    CSV["config/areas_carga.csv<br/>parâmetro versionado"]
    P(("Pipeline"))
    DS["output/dataset<br/>Parquet Snappy"]
    RP["output/reports<br/>quality_report.json"]
    IBGE -. "consulta única em 12/11/2026" .-> CSV
    ONS --> P
    OM --> P
    NG --> P
    CSV --> P
    P --> DS
    P --> RP
```

## 2. Fluxo do pipeline

As etapas, da extração à publicação, com o ponto em que a qualidade pode bloquear.

```mermaid
flowchart TB
    A["Configuração<br/>.env + argumentos"] --> B["Extração<br/>3 APIs"]
    B --> C["Camada bruta<br/>data/raw/*.json"]
    C --> D["Staging SQL<br/>4 UNNEST"]
    D --> E["T1 Tipos e datas"]
    E --> F["T2 Nulos"]
    F --> G["T3 Deduplicação"]
    G --> H["Agregação para hora cheia"]
    H --> I["T4 JOIN"]
    I --> J["T5 Métricas"]
    J --> K{"Qualidade<br/>erro bloqueante?"}
    K -- "não" --> L["Parquet particionado<br/>ano/mês"]
    K -- "sim" --> M["Nada é publicado"]
    L --> N["Relatório JSON"]
    M --> N
    F -. "rejeitados" .-> R["rejeitados_ons"]
```

## 3. Módulos

Dependências entre os módulos Python e os arquivos SQL.

```mermaid
flowchart LR
    main["main.py"] --> config["config.py"]
    main --> extract["extract.py"]
    main --> transform["transform.py"]
    main --> quality["quality.py"]
    main --> persist["persist.py"]
    main --> http["http_client.py"]
    extract --> config
    extract -. "usa get_text" .-> http
    transform --> s1["sql/01_staging.sql"]
    transform --> s2["sql/02_transform.sql"]
```

## 4. Linhagem das tabelas

De qual tabela cada tabela é derivada, dentro do DuckDB.

```mermaid
flowchart LR
    raw_ons --> stg_ons --> t1_ons --> t2_ons --> t3_ons --> carga_horaria
    t1_ons --> rejeitados_ons
    raw_clima --> stg_clima --> t1_clima --> t2_clima --> t3_clima
    raw_feriados --> stg_feriados --> stg_feriados_uf --> t1_feriados --> t3_feriados
    dim_areas --> t3_feriados
    carga_horaria --> t4_cruzado
    dim_areas --> t4_cruzado
    t3_clima --> t4_cruzado
    t3_feriados --> t4_cruzado
    t4_cruzado --> carga_clima_horaria
    carga_horaria --> carga_clima_horaria
```

## 5. Modelo do dataset final

A tabela entregue e as tabelas de apoio que a formam.

```mermaid
erDiagram
    DIM_AREAS ||--o{ CARGA_CLIMA_HORARIA : "cod_areacarga"
    CLIMA |o--|| CARGA_CLIMA_HORARIA : "area + hora_utc"
    FERIADOS |o--o{ CARGA_CLIMA_HORARIA : "dat_referencia + uf"
    CARGA_CLIMA_HORARIA {
        varchar cod_areacarga PK
        timestamp hora_utc PK
        date dat_referencia
        double carga_media_mw
        double temperatura_c
        boolean eh_feriado
        double participacao_mmgd_pct
        int ano
        int mes
    }
    DIM_AREAS {
        varchar cod_areacarga PK
        varchar uf
        double latitude
        double longitude
    }
    CLIMA {
        varchar cod_areacarga PK
        timestamp hora_utc PK
        double temperatura_c
    }
    FERIADOS {
        date data_feriado PK
        varchar uf PK
        varchar nome_feriado
    }
```

## 6. Chamada HTTP com falha transitória

O que acontece quando a API responde 429 e depois se recupera.

```mermaid
sequenceDiagram
    participant E as extract.py
    participant L as RateLimiter
    participant C as HttpClient
    participant A as API
    E->>C: get_text(url)
    C->>L: wait()
    L-->>C: intervalo mínimo cumprido
    C->>A: GET
    A-->>C: 429 com Retry-After 1
    Note over C: espera 1 s
    C->>A: GET (retentativa 1)
    A-->>C: 200 com JSON
    C-->>E: texto da resposta
    Note over C: retentativas = 1 no relatório
```

## 7. Resposta incompleta do ONS

Como a janela é dividida quando faltam dias na resposta.

```mermaid
flowchart TB
    A["Pedir janela início..fim"] --> B{"Vieram todos os dias?"}
    B -- "sim" --> C["Usar os registros"]
    B -- "não" --> D{"Janela de 1 dia?"}
    D -- "sim" --> E["Aviso: sem dado na origem"]
    D -- "não" --> F["Dividir ao meio"]
    F --> A
```

## 8. Hora cheia a partir da meia hora

Por que os instantes 03:30 e 04:00 formam a hora 03:00.

```mermaid
flowchart LR
    a["03:30 UTC<br/>cobre 03:00 a 03:30"] --> h["Hora 03:00 UTC<br/>média dos 2 intervalos"]
    b["04:00 UTC<br/>cobre 03:30 a 04:00"] --> h
    h --> j["JOIN com o clima<br/>de 03:00 UTC"]
```

## 9. Reprocessamento

O que acontece com as partições ao rodar de novo.

```mermaid
flowchart LR
    A["Execução de outubro"] --> B["Apaga ano=2026/mes=10"]
    B --> C["Grava ano=2026/mes=10"]
    D["ano=2026/mes=9"] --- E["Não é tocada"]
```
