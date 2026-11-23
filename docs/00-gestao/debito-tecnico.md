# Débito técnico

Versão 1.1 · 23/11/2026

| ID | Débito | Impacto | Tipo | Prioridade | Ação | Depende de | Status |
|---|---|---|---|---|---|---|---|
| DT-01 | Pipeline nunca executado com as APIs reais | Não há prova de que a extração funciona de ponta a ponta fora do teste; `output/` não existe | Validação | Alta | Rodar o teste rápido e depois a execução completa | Acesso à internet no computador | Resolvido (23/11/2026: execução completa no Windows, 44.160 linhas) |
| DT-02 | README não validado num clone limpo no Windows | Um avaliador pode não conseguir reproduzir | Reprodutibilidade | Alta | Clonar em outra pasta e seguir só o README | DT-01 | Aberto |
| DT-03 | `run.ps1` escrito sem teste | Pode falhar no PowerShell | Validação | Média | Rodar `.\run.ps1 --inicio 2026-10-01 --fim 2026-10-01 --areas PA` | — | Aberto |
| DT-04 | `.vscode/` não aberto no VS Code | Tarefa ou depuração pode precisar de ajuste (ex.: caminho do interpretador) | Validação | Média | Abrir a pasta, selecionar o interpretador e rodar cada tarefa | — | Resolvido (23/11/2026): os 4 JSON são válidos e os comandos das 6 tarefas e das 4 configurações de depuração rodaram no PowerShell do Windows (Python 3.12, duckdb 2.0.0): testes `43 passed`, teste rápido e `--skip-extract` com `success` (42 de 42). Corrigido: o teste rápido gravava em `output/` e trocaria a partição `mes=10` versionada; agora grava em `data/teste-rapido/`. A validar: clicar em Run Task, F5 e Testing dentro do VS Code |
| DT-05 | Versão de Python: mínima 3.11 (exigência do `duckdb` 2.0.0 no PyPI). Testado em 3.13 (duckdb 2.0.0) e 3.12 (duckdb 1.5.6), ambos em Linux | No Windows ainda não testado | Compatibilidade | Média | Registrar a versão usada na execução real no Windows | DT-01 | Resolvido (23/11/2026: Windows, Python 3.12, duckdb 2.0.0) |
| DT-06 | Coordenada = centróide da UF | Clima pouco representativo em UFs grandes (ex.: PA, AM, MT) | Modelo | Baixa | Trocar por coordenada ponderada, com fonte, em `config/areas_carga.csv` | Fonte oficial para o peso | Aceito |
| DT-07 | Partição substituída por inteiro | Reprocessar parte de um mês apaga o restante da partição | Operação | Baixa | Processar meses completos (documentado) ou gravar por dia | — | Aceito |
| DT-08 | `OVERWRITE_OR_IGNORE` não testado com vários arquivos por partição | Com muito volume e várias threads pode sobrar arquivo antigo; hoje a partição é apagada antes, o que evita o caso | Persistência | Baixa | Teste com volume maior | — | Mitigado |
| DT-09 | Sem lint, formatador ou verificação de tipos automática | Estilo e tipos conferidos só por leitura | Qualidade de código | Baixa | Adicionar ruff e mypy com configuração mínima | — | Aberto |
| DT-10 | Sem integração contínua | Testes rodam só na máquina | Automação | Baixa | GitHub Actions com `pytest` | Repositório no GitHub | Aberto |
| DT-11 | Sem dependências travadas por hash | `requirements.txt` fixa só as 5 diretas; as transitivas podem variar | Reprodutibilidade | Baixa | Gerar `pip freeze` no ambiente da execução real | DT-01 | Aberto |
| DT-12 | Intervalos de validade definidos pelo projeto | Limites de clima e carga não vêm de norma | Regra | Baixa | Revisar com os valores observados na execução real | DT-01 | Aceito |
| DT-13 | Extração sequencial | 20 áreas × 3 meses levam alguns minutos por causa do intervalo de 1 s | Desempenho | Baixa | Manter: paralelizar aumentaria o risco de bloqueio | — | Aceito |
| DT-14 | Camada bruta apagada a cada execução | Não há histórico das extrações anteriores | Operação | Baixa | Pasta por `run_id` se o histórico passar a ser necessário | — | Aceito |
| DT-15 | `duckdb` 2.0.0 encerra com "Illegal instruction" ao ser importado no Linux da sessão remota desta máquina (Intel Core i7-870, sem AVX). O `duckdb` 1.5.6 importa e os 43 testes passam | O pipeline pode não rodar nesta máquina com a versão fixada; comportamento no Windows não testado. A linha 1.5 chegou ao fim da vida em 01/11/2026, segundo o calendário do DuckDB | Compatibilidade | Alta | Testar `import duckdb` no Windows. Se falhar, decidir entre fixar `duckdb==1.5.6` ou executar em outra máquina (P-08) | — | Resolvido (23/11/2026: no Windows nativo o 2.0.0 importa, 43 testes passam e o pipeline roda; a falha é só do Linux remoto, também com 2.0.1) |
| DT-16 | O teste rápido pela linha de comando (`run.ps1`, `run.sh` ou `python -m pipeline.main --inicio 2026-10-01 --fim 2026-10-01 --areas PA`) grava em `output/` e substitui a partição `mes=10` versionada (20 áreas) por 24 linhas do PA, além do `quality_report.json` | Quem seguir o README pode estragar o `output/` versionado sem perceber | Operação | Alta | Orientar `OUTPUT_DIR` e `RAW_DIR` separados no README e nos scripts, ou restaurar com `git checkout -- output/` | — | Aberto (achado em 23/11/2026; tratar junto com DT-03) |

## Resumo (23/11/2026)
| Status | Quantidade |
|---|---|
| Aberto | 6 (DT-02, DT-03, DT-09, DT-10, DT-11, DT-16) |
| Mitigado | 1 (DT-08) |
| Aceito | 5 (DT-06, DT-07, DT-12, DT-13, DT-14) |
| Resolvido | 4 (DT-01, DT-04, DT-05, DT-15) |

Os de prioridade Alta ainda abertos (DT-02, DT-16) precisam ser resolvidos antes da entrega.
