# CLAUDE.md — contexto para continuar este projeto no VS Code

Leia este arquivo e `docs/00-gestao/estado-do-projeto.md` antes de qualquer alteração.

## O que é
Desafio Python – FT03 – Projeto 1: pipeline Python + SQL (DuckDB) que cruza carga de energia
(ONS), clima (Open-Meteo) e feriados (Nager.Date) e grava Parquet Snappy particionado por
ano/mês, com relatório de qualidade em JSON. **Entrega: link do repositório público no GitHub
até 23/11/2026 às 08h00.**

## Onde está cada coisa
| Preciso de | Arquivo |
|---|---|
| Situação atual e próximos passos | `docs/00-gestao/estado-do-projeto.md` |
| Decisões tomadas e pendências | `docs/00-gestao/decisoes-e-pendencias.md` |
| Requisitos do enunciado e status | `docs/01-negocio/requisitos.md` |
| Regras de negócio com local no código | `docs/01-negocio/regras-de-negocio.md` |
| Arquitetura, diagramas, ADRs | `docs/02-arquitetura/` |
| APIs (fatos conferidos em chamada real) | `docs/03-tecnico/fontes-de-dados.md` |
| Como rodar, depurar e resolver erro | `docs/03-tecnico/guia-vscode.md`, `docs/03-tecnico/operacao.md` |
| Índice de toda a documentação | `docs/README.md` |

## Comandos
```powershell
python --version                                        # precisa ser 3.11 ou superior
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
.venv\Scripts\python -m pytest -q                       # 43 testes, sem internet
$env:OUTPUT_DIR = "data/teste-rapido/output"; $env:RAW_DIR = "data/teste-rapido/raw"  # não sobrescreve output/
.venv\Scripts\python -m pipeline.main --inicio 2026-10-01 --fim 2026-10-01 --areas PA   # teste rápido real
.venv\Scripts\python -m pipeline.main                   # execução completa (.env)
```
No Git Bash/Linux: `./run.sh`. No PowerShell: `.\run.ps1`.

## Regras de trabalho neste repositório
1. **Nada inferido.** Todo dado vem da API, de cálculo rastreável ou de parâmetro com fonte
   (`config/areas_carga.csv`). Sem fonte = `NULL`, nunca valor suposto.
2. **Fato de API ou de biblioteca só com fonte e data** (documentação oficial ou chamada real).
   O que não foi conferido fica marcado "[a validar]".
3. **Desaninhamento e transformações ficam em SQL** (`sql/`), não em Python: é requisito avaliado.
4. **Toda mudança de regra tem teste** em `tests/` e atualiza `docs/01-negocio/regras-de-negocio.md`.
5. **Credenciais só por variável de ambiente.** Nunca versionar `.env`. Não registrar chave em log.
6. **Rodar `pytest` antes de qualquer commit.** O teste não pode depender das APIs ao vivo.
7. **Não publicar** o PDF do enunciado (tem a marca "Internal"): fica fora do Git (`insumos/*.pdf`).
8. Ao terminar uma sessão: atualizar `estado-do-projeto.md`, `decisoes-e-pendencias.md` e `CHANGELOG.md`.
9. Simplicidade: sem orquestrador, nuvem ou Spark. O escopo é o enunciado.

## Armadilhas já confirmadas
- **Python 3.11 ou superior**: o `duckdb` 2.0.0 não tem pacote para Python 3.10 (PyPI, 12/11/2026).
- **Processador desta máquina (Intel Core i7-870, sem AVX):** o `duckdb` 2.0.0 encerrou com "Illegal
  instruction" no Linux da sessão remota; o 1.5.6 funcionou e os 43 testes passaram (Python 3.12).
  No Windows nativo (23/11/2026, Python 3.12) o 2.0.0 importa e roda: o problema é só do Linux remoto.
- A API do ONS **corta a resposta em silêncio** (HTTP 200) acima de ~2,4 MB: pedir no máximo um
  mês por área e conferir os dias recebidos (`fetch_ons_window` já faz isso).
- DuckDB: `UNNEST` de lista vazia ou nula gera zero linhas (usar `LEFT JOIN LATERAL`);
  `COPY ... OVERWRITE` apaga a raiz inteira (usar `OVERWRITE_OR_IGNORE` e apagar só a partição);
  colunas de partição não ficam dentro do Parquet (`hive_partitioning = true` na leitura).
- O dia de referência do ONS termina às 03:00 UTC do dia seguinte: o clima é extraído com um dia a mais.
- Open-Meteo devolve a coordenada do ponto de grade, não a pedida: a área vem do `meta` do arquivo bruto.

## Situação (23/11/2026)
Pipeline executado com as APIs reais no Windows (01/08 a 31/10/2026, 20 áreas): 44.160 linhas,
3 partições, 41 de 42 verificações aprovadas e 1 aviso (participação MMGD acima de 100% em
MS, MT, PI e RO). Repositório público: https://github.com/ildeanmaster-dot/ft03-pipeline-energia-clima
Falta: enviar o link pelo formulário e validar o README num clone limpo.
