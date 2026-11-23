# Histórico de mudanças

## 0.3.1 — 23/11/2026
- `.vscode/` conferida no Windows (DT-04): JSON válidos; comandos das tarefas e das depurações rodados no PowerShell.
- Tarefa 4 e depuração "teste rápido" passam a gravar em `data/teste-rapido/` (novo no `.gitignore`), sem substituir a partição `mes=10` do `output/` versionado (D-14).
- Registrado DT-16: o teste rápido pela linha de comando ainda grava em `output/`.

## 0.3.0 — 23/11/2026
- Primeira execução com as APIs reais, no Windows (Python 3.12, duckdb 2.0.0): 01/08 a 31/10/2026, 20 áreas, 44.160 linhas, 3 partições, 113 s.
- Relatório: `success_with_warnings`, 41 de 42 verificações aprovadas; aviso em `participacao_mmgd_pct` (376 horas acima de 100% em MS, MT, PI e RO).
- `output/` versionado; repositório público criado no GitHub.
- `duckdb` 2.0.0 confirmado no Windows desta máquina (P-08 e DT-15 encerrados); `.vscode` renomeada (P-09).

## 0.2.1 — 12/11/2026
- Projeto gravado em `D:\Portifolio\DesafioPythonFT03Projeto1` (62 arquivos, conferidos por md5).
- Configuração do VS Code gravada em `_vscode` (renomear para `.vscode`).
- Requisito de Python corrigido para 3.11 ou superior (exigência do `duckdb` 2.0.0).
- Registrado: `duckdb` 2.0.0 falha por instrução ilegal no Linux remoto desta máquina (sem AVX); 1.5.6 funciona, 43 testes passando (DT-15, P-08).

## 0.2.0 — 12/11/2026
- Documentação completa em `docs/` (gestão, negócio, arquitetura, técnica) e índice em `docs/README.md`.
- Configuração do VS Code versionada (`.vscode/`): tarefas, depuração, testes, extensões recomendadas.
- `CLAUDE.md` com o contexto para continuar o projeto com assistente no VS Code.
- `run.ps1` para execução em um comando no PowerShell (ainda não testado, ver DT-03).
- `insumos/README.md`; PDF do enunciado fica fora do Git (`insumos/*.pdf`).

## 0.1.0 — 12/11/2026
- Pipeline completo: extração (ONS, Open-Meteo, Nager.Date), SQL (4 desaninhamentos e
  transformações T1 a T5), qualidade, Parquet Snappy particionado, relatório JSON.
- 43 testes automatizados, incluindo amostras reais das três APIs e um teste ponta a ponta com HTTP.
- `run.sh`, `requirements.txt`, `.env.example`, `README.md`.
- Não executado com as APIs reais (ambiente de construção sem acesso aos domínios).
