# Regras de negócio

Versão 1.0 · 12/11/2026

Origem: **Enunciado** (PDF), **Fonte** (documentação ou comportamento conferido da API),
**Projeto** (decisão deste projeto, registrada em `docs/00-gestao/decisoes-e-pendencias.md`).
Status: **Implementado** = está no código e tem teste; **Provisório** = implementado com
parâmetro a calibrar após a execução real.

## 1. Escopo e parâmetros
| ID | Regra | Origem | Status | Onde está |
|---|---|---|---|---|
| RN-01 | Só entram áreas de carga que o dicionário do ONS nomeia com uma única UF (20 áreas) | Projeto (D-03) | Implementado | `config/areas_carga.csv`; `JOIN dim_areas` em `sql/02_transform.sql` (T4) |
| RN-02 | Área pedida que não está no parâmetro interrompe a execução com erro de configuração | Projeto | Implementado | `load_areas` em `config.py` |
| RN-03 | A coordenada do clima de cada área é o centróide da UF (IBGE Malhas v4) | Projeto (D-04) | Implementado | `config/areas_carga.csv`, coluna `fonte_coordenada` |
| RN-04 | O período é definido pela data de referência do ONS; padrão 01/08 a 31/10/2026 | Projeto (D-05) | Implementado | `load_settings` em `config.py` |
| RN-05 | `DATA_FIM` anterior a `DATA_INICIO` é erro de configuração | Projeto | Implementado | `load_settings` |

## 2. Extração
| ID | Regra | Origem | Status | Onde está |
|---|---|---|---|---|
| RN-06 | O ONS é consultado em janelas que não cruzam a virada de mês | Fonte (OB-01) | Implementado | `month_windows`, `extract_ons` em `extract.py` |
| RN-07 | Todos os dias pedidos ao ONS precisam vir; se faltar algum, a janela é dividida ao meio e pedida de novo, até um dia | Fonte (OB-01) | Implementado | `fetch_ons_window` |
| RN-08 | Dia sem dado na origem (janela de um dia vazia) vira aviso no relatório, não erro | Projeto | Implementado | `fetch_ons_window` |
| RN-09 | Dia com quantidade diferente de 48 registros vira aviso | Fonte (48 intervalos por dia) | Implementado | `extract_ons` |
| RN-10 | Registro do ONS sem os campos obrigatórios interrompe a extração | Projeto | Implementado | `ONS_REQUIRED_FIELDS`, `fetch_ons_window` |
| RN-11 | O clima é extraído com um dia a mais que o período, limitado à data de hoje | Fonte (OB-02) | Implementado | `extract_open_meteo` |
| RN-12 | Os arrays horários do Open-Meteo precisam ter o mesmo tamanho de `time` e o total de horas esperado | Projeto | Implementado | `validate_open_meteo` |
| RN-13 | Intervalo mínimo entre chamadas: 1 s (ONS), 0,5 s (Open-Meteo), 1 s (Nager.Date) | Projeto; limite do Open-Meteo na fonte | Provisório | `.env.example`, `load_settings` |
| RN-14 | 429, 500, 502, 503, 504, timeout e queda de conexão são repetidos até 5 vezes, com espera crescente; `Retry-After` é respeitado até 120 s | Enunciado (retentativas); valores do Projeto | Implementado | `build_retry` em `http_client.py` |
| RN-15 | Demais erros 4xx não são repetidos | Projeto | Implementado | `HttpClient.get_text` |
| RN-16 | JSON inválido por valor ausente é reparado para `null` e registrado como aviso | Projeto (R-05) | Implementado | `parse_json_tolerant` |
| RN-17 | A camada bruta guarda o retorno da API sem alteração, com o que foi pedido e quando | Projeto | Implementado | `write_raw` |

## 3. Transformação
| ID | Regra | Origem | Status | Onde está |
|---|---|---|---|---|
| RN-18 | Datas e instantes são convertidos com `TRY_CAST`; valor inválido vira nulo e é tratado na RN-20 | Projeto | Implementado | T1 |
| RN-19 | Todos os instantes ficam em UTC | Fonte (Swagger do ONS; `timezone=UTC` no Open-Meteo) | Implementado | T1 |
| RN-20 | Registro do ONS com área, data, instante ou carga global nulos é **rejeitado** e contado, com o motivo | Projeto (D-08) | Implementado | T2, tabela `rejeitados_ons` |
| RN-21 | Medida de clima nula é **preservada** como nula; a linha recebe `clima_disponivel = false` | Projeto (D-08) | Implementado | T2 e T4 |
| RN-22 | Nenhum valor é preenchido por suposição (sem média, sem zero no lugar de nulo) | Projeto | Implementado | T2; divisão por zero vira nulo em T5 |
| RN-23 | Registro repetido do ONS (mesma área e instante): vence o de `din_atualizacao` mais recente | Projeto | Implementado | T3 |
| RN-24 | A hora cheia `HH:00` é formada pelos intervalos que terminam em `HH:30` e `(HH+1):00` | Fonte (valor integralizado no fim do intervalo) | Implementado | tabela `carga_horaria` |
| RN-25 | A carga da hora é a média dos intervalos presentes; `qtd_intervalos` informa se foram 1 ou 2 | Projeto | Implementado | tabela `carga_horaria` |
| RN-26 | Carga e clima são cruzados por área e hora UTC; hora sem clima continua no resultado | Projeto (D-07) | Implementado | T4 |
| RN-27 | Só feriados com tipo `Public` contam | Projeto | Implementado | `t1_feriados` |
| RN-28 | Feriado nacional vale para todas as UFs; feriado regional só para a UF indicada | Fonte (campos `global` e `counties`) | Implementado | `t3_feriados` |
| RN-29 | Dois feriados no mesmo dia e UF viram uma linha, com os nomes unidos por " / " | Projeto | Implementado | `t3_feriados` |
| RN-30 | O feriado é associado pela data de referência do ONS, não pela data UTC | Projeto | Implementado | T4 |
| RN-31 | Participação da MMGD = 100 × carga MMGD ÷ carga global; carga zero resulta em nulo | Projeto | Implementado | T5 |
| RN-32 | Variação D-1 = variação percentual contra a mesma hora 24 h antes; sem o dia anterior, nulo | Projeto | Implementado | T5 |
| RN-33 | Dia da semana no padrão ISO (1 = segunda, 7 = domingo); fim de semana = 6 ou 7 | Projeto | Implementado | T5 |

## 4. Qualidade e publicação
| ID | Regra | Origem | Status | Onde está |
|---|---|---|---|---|
| RN-34 | Schema final igual ao contrato (nomes e tipos) | Enunciado | Implementado | `CONTRACT`, `check_schema` em `quality.py` |
| RN-35 | Colunas obrigatórias sem nulos; colunas de clima com até 5% de nulos (aviso) | Enunciado (null ratio); limite do Projeto | Provisório | `CONTRACT`, `check_nulls` |
| RN-36 | Chave (`cod_areacarga`, `hora_utc`) sem repetição | Enunciado | Implementado | `check_uniqueness` |
| RN-37 | Intervalos: temperatura −20 a 55 °C, sensação −30 a 65 °C, umidade 0 a 100%, precipitação 0 a 500 mm | Enunciado (teste de intervalo); limites do Projeto | Provisório | `CONTRACT`, `check_ranges` |
| RN-38 | Carga entre 0 e 100.000 MW e participação MMGD entre 0 e 100% são só aviso | Fonte (OB-04) | Provisório | `CONTRACT` (`range_severity="warning"`) |
| RN-39 | O JOIN não pode multiplicar linhas: linhas finais = horas de carga | Projeto | Implementado | `check_join_and_volume` |
| RN-40 | Menos de 95% das horas com clima gera aviso | Projeto | Provisório | `check_join_and_volume` |
| RN-41 | Saída vazia é erro | Projeto | Implementado | `check_join_and_volume` |
| RN-42 | Verificação com severidade "erro" que falha **bloqueia** a gravação do Parquet | Projeto (D-09) | Implementado | `run_pipeline` em `main.py` |
| RN-43 | O relatório é gravado sempre, inclusive quando a execução falha | Projeto | Implementado | bloco `finally` de `run_pipeline` |
| RN-44 | Reprocessar um período substitui por inteiro as partições (ano, mês) envolvidas e não toca as demais | Projeto (D-10) | Implementado | `write_partitioned` em `persist.py` |
| RN-45 | Nenhuma credencial aparece em log ou mensagem de erro | Enunciado (segurança) | Implementado | `redact` em `http_client.py` |

## 5. Resumo por status
| Status | Quantidade |
|---|---|
| Implementado | 40 |
| Provisório | 5 (RN-13, RN-35, RN-37, RN-38, RN-40: limites a revisar com os valores da execução real) |
| Pendente | 0 |
