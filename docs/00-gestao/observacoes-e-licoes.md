# Observações e lições

Versão 1.1 · 23/11/2026

Cada item traz o que foi observado, o que foi feito e a fonte (documentação ou teste, com data).

| ID | Observação | O que fizemos | Fonte |
|---|---|---|---|
| OB-01 | A API do ONS responde HTTP 200 com JSON válido, mas **cortado**, em períodos longos: PA de 01/06 a 30/09/2026 parou em 15/09 (2,48 MB); de 01/01 a 30/09 parou em 16/04 (2,46 MB). Um mês (0,72 MB) veio completo | Janela de um mês; conferência dos dias; divisão da janela ao meio até um dia (`fetch_ons_window`) | Chamada real, 12/11/2026 |
| OB-02 | O "dia de referência" do ONS vai de 03:30 UTC até 03:00 UTC do dia seguinte (meia-noite a meia-noite em Brasília). O valor é integralizado no fim do intervalo | Hora cheia = `date_trunc('hour', instante − 30 min)`; clima extraído com um dia a mais | Swagger do ONS e chamada real, 12/11/2026 |
| OB-03 | O ONS não envia cabeçalho de limite de taxa nem `Retry-After`, e não publica limite | Intervalo mínimo de 1 s entre chamadas | Chamada real, 12/11/2026 |
| OB-04 | O dicionário do ONS admite `val_cargaglobal` negativo e zerado | Intervalo da carga é só aviso, não erro | PDF do dicionário, 12/11/2026 |
| OB-05 | O dicionário do ONS lista TOCO (Tocantins), que não está entre os 33 códigos do Swagger; TON (Tocantins Norte) está nos dois | Tocantins ficou fora das 20 áreas: TOCO não é aceito pelo contrato da API e TON cobre só parte do estado | Dicionário e Swagger, 12/11/2026 |
| OB-06 | Open-Meteo devolve a coordenada do ponto de grade (−3,9812 pedida → −3,9718807) | A área vem do `meta` do arquivo bruto, nunca da coordenada da resposta | Chamada real, 12/11/2026 |
| OB-07 | Com várias coordenadas numa chamada, a resposta do Open-Meteo vira lista e o primeiro elemento vem sem `location_id` | Uma chamada por área | Chamada real, 12/11/2026 |
| OB-08 | Parâmetro inválido no Open-Meteo devolve HTTP 400 com `{"reason": ..., "error": true}` | 4xx é erro permanente: falha na hora, com o corpo na mensagem | Chamada real, 12/11/2026 |
| OB-09 | Nager.Date: `counties` é `null` no feriado nacional e lista (`BR-SP`) no regional | `LEFT JOIN LATERAL` no desaninhamento para não perder o nacional | Chamada real, 12/11/2026 |
| OB-10 | DuckDB: `UNNEST` de lista vazia ou nula gera zero linhas | Idem OB-09; teste específico | Doc DuckDB 2.0 e teste, 12/11/2026 |
| OB-11 | DuckDB: `COPY ... PARTITION_BY ... OVERWRITE` apagou a raiz inteira (outubro sumiu ao regravar novembro); `OVERWRITE_OR_IGNORE` manteve as outras partições | `OVERWRITE_OR_IGNORE` + apagar só as partições da execução | Teste no DuckDB 2.0.0, 12/11/2026 |
| OB-12 | DuckDB: as colunas de partição não ficam dentro do arquivo Parquet | README e `verify_dataset` leem com `hive_partitioning = true` | Teste no DuckDB 2.0.0, 12/11/2026 |
| OB-13 | DuckDB: Snappy já é a compressão padrão do `COPY` para Parquet | Declarado mesmo assim (`COMPRESSION snappy`) para evidenciar o requisito; conferido por `parquet_metadata` | Doc DuckDB 2.0 e teste, 12/11/2026 |
| OB-14 | `urllib3.Retry`: backoff vem desligado (`backoff_factor=0`) e `status_forcelist` vem vazio | Configurados explicitamente em `build_retry` | Doc urllib3 2.8.0, 12/11/2026 |
| OB-15 | `requests` não tem timeout padrão | Timeout de conexão e de leitura em toda chamada | Comportamento conhecido da biblioteca [a validar na doc] |
| OB-16 | No PA, em 11/10/2026, a geração distribuída chegou a cerca de 32% da carga por volta de 15:00–16:00 UTC | Métrica `participacao_mmgd_pct`; caso usado em teste | Chamada real, 12/11/2026 |
| OB-17 | Com schema fora do contrato, as outras verificações quebram (comparação de texto com número) | Falha de schema encerra as verificações dependentes e já bloqueia | Teste, 12/11/2026 |
| OB-18 | O ambiente de desenvolvimento não tinha acesso às três APIs | Formato validado por amostras reais; a execução real foi feita no Windows em 23/11/2026 | 12/11/2026 |
| OB-19 | `duckdb` 2.0.0 exige Python 3.11 ou superior: com Python 3.10 o `pip` não encontra a versão | README e guia passaram a exigir 3.11+ | PyPI (`requires_python >=3.11.0`) e tentativa de instalação, 12/11/2026 |
| OB-20 | Num ambiente Linux de teste com o processador da máquina do projeto (Intel Core i7-870, só SSE4.2, sem AVX), `import duckdb` na versão 2.0.0 encerra com "Illegal instruction"; as versões 1.5.6 e 1.4.5 importam. Com 1.5.6 e Python 3.12, os 43 testes passam | Registrado como DT-15 e P-08; versão fixada mantida em 2.0.0 até o teste no Windows | Teste, 12/11/2026 |
| OB-22 | Um segundo ambiente Linux de teste também não alcançava as três APIs | A execução real foi feita no Windows em 23/11/2026 | Teste, 12/11/2026 |