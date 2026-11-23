# Testes

Versão 1.1 · 23/11/2026

43 testes com pytest. Nenhum depende das APIs ao vivo: usam dados montados em
`tests/conftest.py`, amostras reais em `tests/fixtures/` e servidores HTTP locais.
Execuções em 12/11/2026, todas com `43 passed`: Python 3.13 + duckdb 2.0.0 (Linux, ambiente de construção) e Python 3.12 + duckdb 1.5.6 (Linux remoto da máquina do projeto). Em 23/11/2026, no Windows (Python 3.12 + duckdb 2.0.0): `43 passed in 24.61s`.

## 1. Como rodar
| Onde | Comando |
|---|---|
| VS Code | Tarefa `3. Rodar testes`, ou a aba Testing |
| PowerShell | `$env:PYTHONPATH = "src"; .venv\Scripts\python -m pytest -q` |
| Git Bash / Linux | `PYTHONPATH=src .venv/bin/python -m pytest -q` |
| Um arquivo | acrescentar `tests/test_transform.py` |
| Um teste | acrescentar `-k nome_do_teste` |

O `pytest.ini` já define `pythonpath = src`; a variável `PYTHONPATH` é redundante com o pytest,
mas necessária para `python -m pipeline.main`.

## 2. O que cada arquivo cobre
| Arquivo | Testes | Cobre |
|---|---|---|
| `test_http_client.py` | 10 | Sucesso; 429 com `Retry-After`; 503 que se recupera; 500 persistente (esgota); 404 sem retentativa; timeout; conexão recusada; limitador de taxa com relógio falso; mascaramento de chave; chave fora da mensagem de erro |
| `test_extract.py` | 8 | Janelas mensais; JSON válido e inválido (sem reparo); resposta do ONS cortada (divisão da janela); dia sem dado; registro sem campo obrigatório; arrays do Open-Meteo de tamanhos diferentes; gravação dos envelopes |
| `test_transform.py` | 13 | Os 3 desaninhamentos; T1; T2 (rejeição e preservação); T3 (ONS e clima); hora cheia; T4 (sem multiplicar, clima ausente, feriados); T5; amostras reais das três APIs |
| `test_quality.py` | 6 | Dataset válido; chave repetida; valor fora do intervalo; nulo em coluna obrigatória; schema divergente; área ausente e clima sem cobertura |
| `test_persist_e_pipeline.py` | 5 | Parquet Snappy particionado; reexecução sem duplicar e sem tocar outra partição; ponta a ponta sem extração; bloqueio por falha de qualidade; relatório em erro de extração |
| `test_integracao_http.py` | 1 | Ponta a ponta com o cliente HTTP real contra um servidor local que devolve 503 na primeira chamada de cada API e corta o ONS em 20 dias |

## 3. Requisito → teste
| Requisito | Teste principal |
|---|---|
| RF-02 Controle de taxa | `test_rate_limiter_espera_o_intervalo_minimo` |
| RF-03 Retentativas | `test_429_respeita_retry_after_e_recupera`, `test_500_persistente_esgota_retentativas`, `test_404_e_erro_permanente_sem_retentativa`, `test_timeout_vira_erro_transitorio` |
| RF-04 Desaninhamento | `test_unnest_ons_...`, `test_unnest_clima_...`, `test_unnest_feriados_...` |
| RF-05 a RF-09 Transformações | `test_t1_...`, `test_t2_...`, `test_t3_...`, `test_t4_...`, `test_t5_...` |
| RF-10 a RF-13 Qualidade | `test_schema_divergente_e_detectado`, `test_nulo_em_coluna_obrigatoria_bloqueia`, `test_chave_duplicada_bloqueia`, `test_valor_fora_do_intervalo_e_detectado` |
| RF-14 Relatório | `test_pipeline_ponta_a_ponta_gera_dataset_e_relatorio` |
| RF-15, RF-16 Parquet | `test_parquet_particionado_snappy` |
| RNF-01 Credenciais | `test_redact_remove_credenciais`, `test_erro_nao_expoe_chave_na_mensagem` |
| Idempotência | `test_reexecucao_nao_duplica_e_preserva_outras_particoes` |

## 4. Dados de teste
- **`tests/conftest.py`:** `ons_records` (48 registros de um dia, carga 1000 + índice),
  `open_meteo_payload`, `holidays_payload` (inclui dois feriados no mesmo dia para SP e um de
  tipo não público), `build_raw` (2 áreas × 2 dias; 12/10 é feriado nacional).
- **`tests/fixtures/`:** respostas reais capturadas em 12/11/2026, com a URL no campo `_origem`:
  6 dos 96 registros do ONS (PA, 11/10/2026), a resposta integral do Open-Meteo para o
  centróide do PA em 11/10/2026 e 2 dos 15 feriados de 2026.

## 5. O que os testes não cobrem
- As APIs reais ao vivo (conferidas à mão na execução de 23/11/2026).
- `run.sh` e `run.ps1` (conferidos à mão em 23/11/2026: DT-03 e DT-16).
- Volume grande e várias threads na gravação (DT-08).

## 6. Regras para novos testes
1. Sem chamada de rede externa.
2. Entrada pequena e saída conferida à mão, com o cálculo no comentário.
3. Um comportamento por teste, com nome em português que diga o que se espera.
4. Toda regra de negócio nova ou alterada ganha teste antes do commit.
