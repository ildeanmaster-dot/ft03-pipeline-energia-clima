# Requisitos

Versão 1.0 · 12/11/2026

Fonte: enunciado `FT03_Engenharia_PRJ01_Python.pdf`, seções 2 a 5. Prioridade "Obrig." = exigido
pelo enunciado. Status por evidência: **Implementado** = código e teste existem;
**Parcial** = feito, falta uma validação; **Pendente** = não feito.

## 1. Requisitos funcionais
| ID | Requisito | Seção | Prior. | Status | Evidência |
|---|---|---|---|---|---|
| RF-01 | Consumir no mínimo 2 APIs públicas de domínios distintos | 2.1 | Obrig. | Implementado | 3 APIs (energia, clima, calendário) em `src/pipeline/extract.py`; Execução real em 23/11/2026: 20 áreas ONS e Open-Meteo, feriados Nager.Date |
| RF-02 | Controle de taxa (rate limiting) | 2.1 | Obrig. | Implementado | `RateLimiter` em `http_client.py`; `test_rate_limiter_espera_o_intervalo_minimo` |
| RF-03 | Retentativas com tratamento de erros | 2.1 | Obrig. | Implementado | `build_retry` e `HttpClient.get_text`; testes de 429, 503, 500, 404, timeout e conexão |
| RF-04 | Desaninhamento de coleções complexas via SQL | 2.2 | Obrig. | Implementado | 4 `UNNEST` em `sql/01_staging.sql`; 3 testes de UNNEST |
| RF-05 | Transformação: padronização de tipos e datas | 2.2 | Obrig. | Implementado | T1 em `sql/02_transform.sql`; `test_t1_tipos_e_datas` |
| RF-06 | Transformação: tratamento de nulos | 2.2 | Obrig. | Implementado | T2; `test_t2_nulos_...`, `test_t2_clima_nulo_...` |
| RF-07 | Transformação: deduplicação | 2.2 | Obrig. | Implementado | T3; `test_t3_deduplicacao_vence_o_registro_mais_recente` |
| RF-08 | Transformação: cruzamento de fontes (JOIN) | 2.2 | Obrig. | Implementado | T4; `test_t4_join_nao_multiplica_linhas_...` |
| RF-09 | Transformação: enriquecimento de métricas | 2.2 | Obrig. | Implementado | T5; `test_t5_metricas_derivadas` |
| RF-10 | Validação de schema | 2.3 | Obrig. | Implementado | `check_schema` e schema de leitura declarado no SQL; `test_schema_divergente_e_detectado` |
| RF-11 | Cálculo de null ratio | 2.3 | Obrig. | Implementado | `null_ratios`, `check_nulls`; `test_nulo_em_coluna_obrigatoria_bloqueia` |
| RF-12 | Verificação de unicidade | 2.3 | Obrig. | Implementado | `check_uniqueness`; `test_chave_duplicada_bloqueia` |
| RF-13 | Testes de intervalo | 2.3 | Obrig. | Implementado | `check_ranges`; `test_valor_fora_do_intervalo_e_detectado` |
| RF-14 | Relatório resumido de execução e auditoria de qualidade em JSON ou CSV | 2.3 | Obrig. | Implementado | `output/reports/quality_report.json` (execução real em 23/11/2026, `success_with_warnings`) |
| RF-15 | Camada final em formato colunar (Parquet ou Delta) com Snappy | 2.3 | Obrig. | Implementado | `output/dataset/` com Snappy; 3 arquivos Parquet |
| RF-16 | Particionamento temporal (ex.: ano/mês) | 2.3 | Obrig. | Implementado | `output/dataset/ano=2026/mes=8`, `mes=9`, `mes=10` |

## 2. Requisitos não funcionais
| ID | Requisito | Seção | Prior. | Status | Evidência |
|---|---|---|---|---|---|
| RNF-01 | Credenciais só por variável de ambiente (.env ou os.getenv), sem commit de chaves | 2.1 | Obrig. | Implementado | `config.py`, `.env.example`, `.gitignore`; `test_erro_nao_expoe_chave_na_mensagem` |
| RNF-02 | Scripts modulares em Python, funções limpas | 2.2 | Obrig. | Implementado | 7 módulos em `src/pipeline/`, um por responsabilidade |
| RNF-03 | Type hints | 2.2 | Obrig. | Implementado | Todas as funções de `src/pipeline/` são anotadas (conferência por leitura; sem mypy, DT-09) |
| RNF-04 | Repositório Git com estrutura modular em `src/`, no GitHub | 3 | Obrig. | Implementado | https://github.com/ildeanmaster-dot/ft03-pipeline-energia-clima (23/11/2026) |
| RNF-05 | README com instruções de execução, variáveis de ambiente e documentação das APIs | 3 | Obrig. | Implementado | `README.md`, seções 1 e 3 |
| RNF-06 | `requirements.txt` para reprodução exata | 3 | Obrig. | Implementado | Versões fixadas com `==` |
| RNF-07 | `run.sh` ou comando único ponta a ponta | 3 | Obrig. | Implementado | `run.sh` testado em Linux; no Windows, `python -m pipeline.main` executado em 23/11/2026 (`run.ps1` não testado, DT-03) |
| RNF-08 | Dataset em `output/` (.parquet) | 3 | Obrig. | Implementado | 3 partições, 44.160 linhas (23/11/2026) |
| RNF-09 | Relatório de qualidade em JSON ou CSV entregue | 3 | Obrig. | Implementado | `output/reports/quality_report.json` |
| RNF-10 | Repositório público | 5 | Obrig. | Implementado | https://github.com/ildeanmaster-dot/ft03-pipeline-energia-clima |
| RNF-11 | Link enviado até 23/11/2026 às 08h00 pelo formulário | 5 | Obrig. | Pendente | P-03 |
| RNF-12 | Reprodutibilidade do pipeline (critério de avaliação) | 4 | Obrig. | Implementado | Clone limpo do GitHub no Windows em 23/11/2026, seguindo só o README: `43 passed` e execução completa `success_with_warnings` (41 de 42), com Parquet idênticos byte a byte aos versionados (DT-02) |
| RNF-13 | Robustez a exceções HTTP e falhas (critério de avaliação) | 4 | Obrig. | Implementado | `tests/test_http_client.py`, `tests/test_integracao_http.py` |
| RNF-14 | Governança: schema, integridade, relatório descritivo (critério de avaliação) | 4 | Obrig. | Implementado | `quality.py`; política de bloqueio; `test_falha_de_qualidade_bloqueia_publicacao_...` |

## 3. Resumo por status
| Status | RF | RNF | Total |
|---|---|---|---|
| Implementado | 16 | 13 | 29 |
| Parcial | 0 | 0 | 0 |
| Pendente | 0 | 1 | 1 |

Situação em 23/11/2026: reprodutibilidade confirmada num clone limpo (RNF-12); falta enviar
o link pelo formulário (RNF-11).
