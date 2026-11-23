# Operação

Versão 1.0 · 12/11/2026

## 1. Executar
| Situação | Comando (Git Bash / Linux) | Comando (PowerShell) |
|---|---|---|
| Período e áreas do `.env` | `./run.sh` | `.\run.ps1` |
| Teste rápido | `./run.sh --inicio 2026-10-01 --fim 2026-10-01 --areas PA` | `.\run.ps1 --inicio 2026-10-01 --fim 2026-10-01 --areas PA` |
| Outro período | `./run.sh --inicio 2026-07-01 --fim 2026-07-31` | idem com `.\run.ps1` |
| Sem chamar as APIs | `./run.sh --skip-extract` | `.\run.ps1 --skip-extract` |

`run.ps1` ainda não foi testado (DT-03). Alternativa garantida: os três comandos do README.

Os argumentos de linha de comando têm prioridade sobre o `.env`.

## 2. Código de saída e status
| Código | `status` no relatório | Significado |
|---|---|---|
| 0 | `success` | Tudo certo |
| 0 | `success_with_warnings` | Publicado, com avisos a ler |
| 1 | `failed_quality` | Verificação bloqueante falhou; nada publicado |
| 1 | `failed` | Erro de extração, de SQL ou de gravação |
| 2 | (sem relatório) | Configuração inválida; a mensagem aparece no log |

## 3. Duração esperada
Dominada pelo intervalo entre chamadas. Com o padrão (cerca de 140 chamadas; 1 s no ONS e
0,5 s no Open-Meteo): alguns minutos, mais o tempo de resposta das APIs. A transformação e a
gravação levam segundos. Tempo real **[a medir na primeira execução]**.

## 4. Reprocessar
- **Mesmo período:** rode de novo. As partições do período são apagadas e regravadas; o
  resultado é o mesmo, sem duplicar.
- **Outro mês:** as partições já gravadas não são tocadas.
- **Parte de um mês:** a partição do mês passa a conter só o recorte extraído. Para manter o
  mês inteiro, processe o mês inteiro.
- **Só transformação e qualidade:** `--skip-extract` usa o que está em `data/raw/`.
- **Recomeçar do zero:** apague `output/dataset/` e rode de novo.

## 5. Solução de problemas
| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `Configuração inválida: DATA_INICIO deve estar no formato AAAA-MM-DD` | Data mal escrita no `.env` ou no argumento | Corrigir o formato |
| `Áreas sem coordenada em areas_carga.csv: XX` | Área pedida fora do parâmetro | Usar uma das 20 áreas ou acrescentar a linha no CSV, com fonte |
| `TransientHTTPError: ... timeout ou falha de conexão` | Sem internet, proxy ou firewall bloqueando o domínio | Abrir a URL do erro no navegador; liberar `apicarga.ons.org.br`, `archive-api.open-meteo.com`, `date.nager.at` |
| `TransientHTTPError: ... retentativas esgotadas` | API instável ou limite de taxa | Esperar e rodar de novo; aumentar `ONS_MIN_INTERVAL_S` ou `HTTP_MAX_RETRIES` |
| `PermanentHTTPError: ... HTTP 400` | Parâmetro recusado pela API (a mensagem traz o motivo) | Conferir datas e coordenadas; data futura não tem dado |
| `PermanentHTTPError: ... HTTP 404` | Endpoint mudou | Conferir a documentação em `fontes-de-dados.md` |
| `ExtractionError: Open-Meteo ...: N horas, esperado M` | A API devolveu menos horas (período muito recente) | Recuar `DATA_FIM` |
| `ExtractionError: ... registro sem os campos obrigatórios` | O ONS mudou o formato | Comparar a resposta com `fontes-de-dados.md`; ajustar `ONS_REQUIRED_FIELDS` e o schema do SQL |
| Aviso `ONS sem dados na origem para X em AAAA-MM-DD` | A origem não tem aquele dia | Conferir no navegador; se confirmar, é lacuna da fonte |
| Aviso `JSON com valor ausente reparado` | O ONS devolveu um campo sem valor | O registro entra com nulo e é rejeitado em T2 se for a carga |
| Erro do DuckDB `No files found that match the pattern` | `data/raw/` vazio com `--skip-extract` | Rodar sem `--skip-extract` |
| Erro do DuckDB de conversão ao ler JSON | Campo com tipo diferente do declarado | Ver o campo na mensagem; ajustar o schema em `sql/01_staging.sql` |
| `status: failed_quality` | Verificação bloqueante falhou | Ler `verificacoes` com `passed: false` e `severity: error` |
| `join_cobertura_clima` abaixo de 0,95 | Clima ausente para parte das horas | Conferir se o período é muito recente e se o clima foi extraído até o dia seguinte |
| `dias_com_24_horas_completas` maior que 0 | Dia com menos de 48 registros no ONS | Ver os avisos da extração |
| `No matching distribution found for duckdb==2.0.0` | Python 3.10 ou anterior | Instalar Python 3.11 ou superior e recriar a `.venv` |
| O programa encerra sozinho ao iniciar, sem mensagem, ou com "Illegal instruction" | Processador sem AVX com o `duckdb` 2.0.0 (DT-15) | Trocar para `duckdb==1.5.6` no `requirements.txt` e reinstalar |
| `ModuleNotFoundError: No module named 'pipeline'` | `PYTHONPATH` sem `src` | `$env:PYTHONPATH = "src"` ou usar as tarefas do VS Code |
| PowerShell: "a execução de scripts foi desabilitada" | Política de execução | `powershell -ExecutionPolicy Bypass -File .\run.ps1` |
| Erro de permissão ao apagar a partição | Arquivo Parquet aberto em outro programa | Fechar o programa e rodar de novo |

## 6. Depois de cada execução para entrega
1. Ler o relatório (roteiro em `qualidade-de-dados.md`, seção 4).
2. Rodar `python scripts/inspecionar_dataset.py` e conferir as áreas e as horas.
3. Atualizar `estado-do-projeto.md` com os números reais.
4. Fazer o commit do `output/`.

## 7. Arquivos gerados
| Caminho | Versionado? | Pode apagar? |
|---|---|---|
| `data/raw/` | Não | Sim; é refeito pela extração |
| `output/dataset/` | Sim | Sim; é refeito pela execução |
| `output/reports/quality_report.json` | Sim | É sobrescrito a cada execução |
| `.venv/` | Não | Sim; é refeito pelo `run.sh` |
