# Guia de continuidade no VS Code

Versão 1.1 · 23/11/2026

Passos numerados, com o resultado esperado de cada um. Em 23/11/2026 os comandos das tarefas e
das configurações de depuração foram conferidos no PowerShell do Windows (DT-04); a execução
pelos menus do VS Code (Run Task, F5, Testing) ainda está "A validar".

## 1. Preparar (uma vez)
| # | Ação | Resultado esperado |
|---|---|---|
| 1 | Conferir a pasta do projeto: `D:\Portifolio\DesafioPythonFT03Projeto1` (gravada em 12/11/2026) | A pasta contém `src`, `sql`, `tests`, `docs`, `.vscode`, `README.md` |
| 2 | No Explorador de Arquivos do Windows, renomear a pasta `_vscode` para `.vscode` (ou, no PowerShell, dentro da pasta: `Rename-Item _vscode .vscode`) | Existe a pasta `.vscode` com 4 arquivos `.json`. A ferramenta que gravou os arquivos não pode escrever em `.vscode`, por isso o nome provisório |
| 3 | No PowerShell: `python --version` | Versão **3.11 ou superior**. Com 3.10 ou anterior o `duckdb` 2.0.0 não instala |
| 4 | VS Code → **File > Open Folder** → escolher essa pasta | O Explorer mostra a raiz do projeto |
| 5 | Aceitar a sugestão de instalar as extensões recomendadas | Python, Pylance, Python Debugger e Markdown Preview Mermaid Support instaladas |
| 6 | **Terminal > Run Task** → `1. Criar ambiente (.venv)` | Surge a pasta `.venv` |
| 7 | `Ctrl+Shift+P` → **Python: Select Interpreter** → escolher `.venv\Scripts\python.exe` | A barra de status mostra o Python da `.venv` |
| 8 | **Run Task** → `2. Instalar dependências` | Termina sem erro; `pip list` mostra `duckdb 2.0.0` |
| 9 | No terminal do VS Code: `.venv\Scripts\python -c "import duckdb; print(duckdb.__version__)"` | Imprime `2.0.0`. **Se o comando encerrar sem imprimir nada ou com erro de instrução ilegal**, o processador não é aceito por essa versão: troque `duckdb==2.0.0` por `duckdb==1.5.6` no `requirements.txt` e repita o passo 8 (ver DT-15) |
| 10 | (Opcional) Copiar `.env.example` para `.env` | Arquivo `.env` na raiz; ele não aparece no `git status` |
| 11 | Abrir um terminal novo no VS Code | `echo $env:PYTHONPATH` mostra o caminho de `src` |

## 2. Conferir que está tudo certo
| # | Ação | Resultado esperado |
|---|---|---|
| 1 | **Run Task** → `3. Rodar testes` | `43 passed` (cerca de 10 s; não usa internet) |
| 2 | Ícone do béquer (Testing) na barra lateral | Árvore com 6 arquivos de teste; todos verdes ao rodar |
| 3 | **Run Task** → `4. Pipeline: teste rápido (PA, 1 dia)` | Última linha: `Status final: success`; surgem `data/teste-rapido/output/dataset/ano=2026/mes=10/` (24 linhas) e `data/teste-rapido/output/reports/quality_report.json`. O `output/` versionado não é tocado |

A tarefa 4 e a depuração "teste rápido" gravam em `data/teste-rapido/` (fora do Git) de
propósito: o pipeline substitui a partição do mês inteiro (D-10), e rodar o teste rápido em
`output/` trocaria a partição `mes=10` das 20 áreas por 24 linhas do PA.

Se o passo 3 falhar, veja `docs/03-tecnico/operacao.md`, seção "Solução de problemas".

## 3. Execução completa
| # | Ação | Resultado esperado |
|---|---|---|
| 1 | **Run Task** → `5. Pipeline: execução completa (.env)` (ou `Ctrl+Shift+B`) | Alguns minutos; uma linha de log por área extraída; `Status final: success` ou `success_with_warnings` |
| 2 | Abrir `output/reports/quality_report.json` | `falhas_bloqueantes: 0`; `linhas_no_dataset: 44160` com o período padrão completo; `compressao: ["SNAPPY"]` |
| 3 | Conferir `docs/00-gestao/checklist-de-entrega.md` | Itens da seção "Antes de publicar" marcados |

## 4. Depurar
Aba **Run and Debug** (`Ctrl+Shift+D`), configurações prontas em `.vscode/launch.json`:

| Configuração | Quando usar |
|---|---|
| Pipeline: período padrão (.env) | Depurar a execução completa |
| Pipeline: teste rápido (PA, 1 dia) | Depurar com chamadas reais, em segundos (grava em `data/teste-rapido/`) |
| Pipeline: sem extração (reusa data/raw) | Depurar SQL, qualidade e gravação sem chamar as APIs |
| Testes: arquivo atual | Depurar o arquivo de teste aberto |

Pontos de parada úteis: `fetch_ons_window` (extração), `run_transformations` (antes do SQL),
`run_quality_checks` (resultado das verificações), `write_partitioned` (gravação).

## 5. Inspecionar os dados
No terminal do VS Code, com a `.venv` selecionada:

```powershell
.venv\Scripts\python scripts\inspecionar_dataset.py
```

Resultado esperado: as partições com a quantidade de linhas, uma linha por área (2.208 horas
cada no período padrão), a compressão `SNAPPY` e `Chaves repetidas: 0`.

Para examinar as tabelas intermediárias, use a configuração "sem extração" com ponto de
parada depois de `run_transformations` e consulte pelo Debug Console:
`con.sql("SELECT * FROM rejeitados_ons").show()`.

## 6. Onde mexer para cada tipo de mudança
| Quero | Arquivo | Não esquecer |
|---|---|---|
| Mudar período ou áreas | `.env` | — |
| Acrescentar ou corrigir uma área | `config/areas_carga.csv` | Preencher as colunas de fonte |
| Mudar uma regra de transformação | `sql/02_transform.sql` | Teste em `tests/test_transform.py`; `regras-de-negocio.md` |
| Acrescentar uma coluna | `sql/02_transform.sql` + `CONTRACT` em `quality.py` | `dicionario-de-dados.md`; README, seção 5 |
| Mudar um limite de qualidade | `CONTRACT` em `quality.py` | `qualidade-de-dados.md`; `regras-de-negocio.md` |
| Acrescentar uma variável de clima | `HOURLY_VARIABLES` em `extract.py` + schema em `sql/01_staging.sql` + T1 | Fixtures em `tests/conftest.py` |
| Acrescentar uma API | Função `extract_*` em `extract.py` + entrada em `run_extraction` (`main.py`) + SQL | `fontes-de-dados.md`; teste |
| Ajustar retentativa ou taxa | `.env` (valores) ou `build_retry` (`http_client.py`) | `tests/test_http_client.py` |

## 7. Git (iniciado em 23/11/2026; remoto: https://github.com/ildeanmaster-dot/ft03-pipeline-energia-clima)
| # | Ação | Resultado esperado |
|---|---|---|
| 1 | `git init -b main` | Pasta `.git` criada |
| 2 | `git status` | Não lista `.env`, `.venv/`, `data/raw/` nem `insumos/*.pdf` |
| 3 | `git add .` e `git commit -m "Pipeline carga x clima x feriados"` | Commit criado |
| 4 | Criar o repositório público no GitHub e `git remote add origin <url>` | `git remote -v` mostra a URL |
| 5 | `git push -u origin main` | Arquivos visíveis no GitHub |

Faça o commit do `output/` só depois da execução completa conferida.

## 8. Ao encerrar uma sessão de trabalho
1. Rodar os testes.
2. Atualizar `docs/00-gestao/estado-do-projeto.md` e `decisoes-e-pendencias.md`.
3. Registrar a mudança no `CHANGELOG.md`.
4. Fazer o commit.

## 9. Trabalhar com assistente de IA no VS Code
O arquivo `CLAUDE.md`, na raiz, traz o contexto, os comandos, as regras e as armadilhas já
confirmadas. Peça ao assistente para ler `CLAUDE.md` e `docs/00-gestao/estado-do-projeto.md`
antes de qualquer alteração.
