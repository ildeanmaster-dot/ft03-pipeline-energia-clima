# Histórico de mudanças

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
