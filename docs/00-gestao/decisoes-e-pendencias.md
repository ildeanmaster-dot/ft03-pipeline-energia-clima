# Decisões e pendências

Versão 1.1 · 23/11/2026

## 1. Decisões
| # | Decisão | Data | Situação |
|---|---|---|---|
| D-01 | Fontes: ONS Carga Verificada (energia) + Open-Meteo Historical (clima) | 12/11/2026 | Aprovada pelo responsável |
| D-02 | Nager.Date (feriados) entra como terceira fonte | 12/11/2026 | Aprovada pelo responsável |
| D-03 | Áreas: as 20 que o dicionário do ONS nomeia com uma única UF | 12/11/2026 | Aprovada pelo responsável |
| D-04 | Coordenada de cada área: centróide da UF pela API de Malhas do IBGE, em `config/areas_carga.csv` | 12/11/2026 | Aprovada pelo responsável |
| D-05 | Período padrão: 01/08 a 31/10/2026, alterável no `.env` | 12/11/2026 | Aprovada pelo responsável |
| D-06 | Tecnologia: Python + DuckDB + Parquet, sem orquestrador nem nuvem | 12/11/2026 | Adotada (ADR-01) |
| D-07 | Granularidade: 1 linha = área × hora UTC; a meia hora do ONS é agregada para hora cheia | 12/11/2026 | Adotada (ADR-04) |
| D-08 | Nulo em chave ou carga rejeita o registro; nulo de clima é preservado. Nada é preenchido por suposição | 12/11/2026 | Adotada (ADR-05) |
| D-09 | Falha de qualidade com severidade "erro" bloqueia a publicação do Parquet | 12/11/2026 | Adotada (ADR-06) |
| D-10 | Reprocessamento substitui a partição inteira do mês (apaga e regrava) | 12/11/2026 | Adotada (ADR-07) |
| D-11 | Extração do ONS em janelas de um mês, com divisão automática quando faltam dias | 12/11/2026 | Adotada (ADR-03) |
| D-12 | O PDF do enunciado (marca "Internal") não é versionado | 12/11/2026 | Adotada |
| D-13 | A pasta `.vscode/` é versionada (tarefas, depuração, testes) | 12/11/2026 | Adotada |
| D-14 | O teste rápido do VS Code (tarefa 4 e depuração) grava em `data/teste-rapido/` (fora do Git), para não substituir a partição `mes=10` do `output/` versionado | 23/11/2026 | Adotada (DT-04) |
| D-15 | Simplificações após revisão de complexidade: sem reparo automático de JSON; clima repetido decidido pela extração mais recente (RN-46); sem a variável `AREAS_FILE`; `assert` trocado em `quality.py`; README (tabela de qualidade) e RNF-07 corrigidos. Dataset final idêntico byte a byte | 23/11/2026 | Aprovada pelo responsável |
| D-16 | Licença do repositório: MIT (código e documentação); dados em `output/` seguem as licenças das fontes | 23/11/2026 | Aprovada pelo responsável |

## 2. Pendências
| # | Pendência | Bloqueia | Com quem | Desde |
|---|---|---|---|---|
| P-01 | **Resolvida em 23/11/2026:** execução real no Windows, `output/` gerado. Executar o pipeline com as APIs reais e gerar `output/` | Entregas E5 e E6 | Freitas | 12/11/2026 |
| P-02 | **Resolvida em 23/11/2026:** https://github.com/ildeanmaster-dot/ft03-pipeline-energia-clima Criar o repositório público no GitHub (conta `ildeanmaster-dot`) e definir o nome (sugestão: `ft03-pipeline-energia-clima`) | Entrega E1 | Freitas | 12/11/2026 |
| P-03 | Receber o link do formulário de entrega | Envio | Organização do desafio | 12/11/2026 |
| P-04 | **Resolvida em 23/11/2026:** `.vscode/` conferida (menus do VS Code a validar, DT-04) e `run.ps1` testado e corrigido (DT-03). Validar `run.ps1` e a configuração `.vscode/` no Windows | Não bloqueia a entrega (o `run.sh` atende) | Freitas | 12/11/2026 |
| P-05 | **Encerrada em 23/11/2026:** fora do escopo do desafio. Decidir se o projeto terá portal de acompanhamento | Não bloqueia | Freitas | 12/11/2026 |
| P-06 | **Resolvida em 23/11/2026:** versionado completo (20 áreas, 3 meses, ~1,7 MB). Decidir se o `output/` versionado terá as 20 áreas e os 3 meses ou um recorte menor | Tamanho do repositório | Freitas | 12/11/2026 |
| P-07 | Confirmar com quem emitiu o enunciado se o PDF pode ser publicado | Não bloqueia | Freitas | 12/11/2026 |
| P-08 | **Resolvida em 23/11/2026:** mantido 2.0.0, que funciona no Windows desta máquina. Versão do `duckdb`: manter 2.0.0 (LTS atual; falhou no Linux remoto desta máquina por falta de AVX) ou fixar 1.5.6 (funciona aqui; linha fora de suporte desde 01/11/2026). Depende do teste de `import duckdb` no Windows | Execução nesta máquina (P-01) | Freitas | 12/11/2026 |
| P-09 | **Resolvida em 23/11/2026:** pasta de configuração do VS Code com o nome definitivo `.vscode` | Tarefas e depuração no VS Code | Freitas | 12/11/2026 |
| P-10 | **Resolvida em 23/11/2026:** mantidas as variáveis de ajuste HTTP e a chave opcional do Open-Meteo; mantido o bloqueio por carga MMGD fora da faixa, porque o dicionário do ONS (versão 1.1, 30/10/2023, p. 2) não admite `val_cargammgd` negativo (e admite `val_cargaglobal` negativo) (RN-47) | Não bloqueia | Freitas | 23/11/2026 |