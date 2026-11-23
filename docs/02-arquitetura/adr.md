# Registro de decisões de arquitetura (ADR)

Versão 1.0 · 12/11/2026

Formato: contexto, opções, decisão, consequências. Todas com data de 12/11/2026 e situação "Aceita".

## ADR-01 — Python + DuckDB + Parquet
- **Contexto:** o enunciado pede Python, SQL para desaninhar (cita DuckDB, SQLite e PySpark) e saída em Parquet ou Delta com Snappy.
- **Opções:** (a) DuckDB; (b) SQLite + pyarrow; (c) PySpark + Delta.
- **Decisão:** DuckDB 2.0.0.
- **Consequências:** lê JSON aninhado, tem `UNNEST` e grava Parquet Snappy particionado sem outra biblioteca; roda em memória, sem instalação. Abre-se mão de processamento distribuído e de Delta Lake, desnecessários para dezenas de milhares de linhas.

## ADR-02 — Três fontes, sendo duas obrigatórias
- **Contexto:** o mínimo são duas APIs de domínios distintos, com JOIN que faça sentido e estrutura aninhada.
- **Opções:** só ONS + Open-Meteo; ou acrescentar feriados.
- **Decisão:** ONS (energia) + Open-Meteo (clima) + Nager.Date (calendário).
- **Consequências:** o JOIN carga × clima responde à pergunta; os feriados acrescentam um segundo desaninhamento (`counties[]`) e um JOIN por data. Custo: uma dependência externa a mais, de projeto comunitário.

## ADR-03 — Janelas mensais com divisão automática no ONS
- **Contexto:** a API corta a resposta em silêncio acima de cerca de 2,4 MB (OB-01).
- **Opções:** (a) janela fixa de um mês e confiar; (b) janela de um dia sempre; (c) janela mensal com conferência e divisão.
- **Decisão:** (c).
- **Consequências:** poucas chamadas no caso normal e nenhuma perda silenciosa. Se a origem não tiver dado para um mês inteiro, o pipeline desce até janelas de um dia antes de registrar o aviso (mais chamadas nesse caso raro).

## ADR-04 — Granularidade horária em UTC
- **Contexto:** o ONS é semi-horário e o Open-Meteo é horário.
- **Opções:** (a) agregar a carga para hora; (b) repetir o clima nos dois intervalos de 30 min.
- **Decisão:** (a), com a hora `HH:00` formada pelos intervalos que terminam em `HH:30` e `(HH+1):00`.
- **Consequências:** nenhuma linha de clima é duplicada e a chave do JOIN é exata. Perde-se o detalhe de 30 minutos; `carga_max_mw` e `qtd_intervalos` preservam parte da informação.

## ADR-05 — Nulo rejeita ou é preservado; nunca é preenchido
- **Contexto:** o enunciado pede tratamento de nulos; preencher com média ou zero cria dado que não existe na origem.
- **Decisão:** nulo em chave ou carga rejeita o registro (contado em `rejeitados_ons`); nulo em clima é mantido e sinalizado em `clima_disponivel`.
- **Consequências:** o dataset nunca contém valor suposto. Quem analisa precisa tratar os nulos de clima conforme o método de análise.

## ADR-06 — Qualidade com duas severidades e bloqueio de publicação
- **Contexto:** nem toda anomalia invalida o dataset (o próprio ONS admite carga negativa).
- **Decisão:** "erro" bloqueia a gravação do Parquet; "aviso" é registrado. O relatório é gravado sempre.
- **Consequências:** nunca se publica um dataset com chave repetida, schema errado ou JOIN multiplicado. Limites marcados como aviso precisam ser lidos por uma pessoa.

## ADR-07 — Reprocessamento por substituição de partição
- **Contexto:** `COPY ... OVERWRITE` do DuckDB apaga a raiz inteira (OB-11).
- **Opções:** (a) apagar tudo e regravar; (b) acrescentar arquivos; (c) apagar só as partições da execução e gravar com `OVERWRITE_OR_IGNORE`.
- **Decisão:** (c).
- **Consequências:** reexecução não duplica e não afeta outros meses. Processar parte de um mês substitui a partição inteira pelo recorte extraído (DT-07).

## ADR-08 — Camada bruta em arquivos, limpa a cada execução
- **Decisão:** um arquivo JSON por área e janela, com envelope `meta` + `payload`; a pasta é limpa no início de cada execução.
- **Consequências:** a transformação enxerga só a execução atual e pode ser refeita com `--skip-extract`. Não há histórico de extrações (DT-14).

## ADR-09 — Coordenada por arquivo de parâmetro
- **Contexto:** nenhuma API relaciona área de carga a coordenada.
- **Opções:** (a) coordenadas no código; (b) chamar o IBGE a cada execução; (c) arquivo CSV versionado com a fonte por linha.
- **Decisão:** (c).
- **Consequências:** o vínculo é explícito, auditável e editável sem tocar no código; a execução depende de uma API a menos. O arquivo precisa ser atualizado à mão se o critério mudar.

## ADR-10 — Regras em arquivos SQL, orquestração em Python
- **Decisão:** todo desaninhamento e toda transformação ficam em `sql/`; o Python só extrai, executa o SQL, valida e grava.
- **Consequências:** o domínio de SQL fica evidente para a avaliação e as regras são lidas num lugar só. Os caminhos chegam ao SQL por `SET VARIABLE`.

## ADR-11 — Cliente HTTP sobre requests + urllib3.Retry
- **Opções:** (a) laço de retentativa próprio; (b) biblioteca `tenacity`; (c) `urllib3.Retry` no adaptador do `requests`.
- **Decisão:** (c), mais um limitador de taxa próprio de poucas linhas.
- **Consequências:** backoff, jitter e `Retry-After` vêm de implementação madura, sem dependência extra. O limitador é simples (intervalo mínimo), suficiente para execução sequencial.
