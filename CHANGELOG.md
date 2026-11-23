# Histórico de mudanças

## 0.4.1 — 23/11/2026
- Licença MIT (`LICENSE`) para código e documentação; README seção 10 e `custos-e-licencas.md` atualizados (D-16).
- Validação completa por 3 revisores independentes (código, dados, documentação): nenhum achado bloqueante; recálculo independente das 44.160 linhas sem divergência.
- Documentação alinhada ao estado de 23/11: checklist marcado, visão geral, riscos, roadmap, termo, operação, testes e guia do VS Code sem "pendente"/"não testado"; README com o resultado entregue, tempo de execução e resumo do dataset.
- Documentado: precipitação é a soma da hora anterior (DT-19); `--skip-extract` não filtra período e áreas (DT-18); a chave opcional pode aparecer no log do `urllib3` (DT-17); `ano`/`mes` lidos como BIGINT; só feriados nacionais no período; nova RN-47 (MMGD fora da faixa bloqueia).
- `.gitattributes` com `*.sh text eol=lf`; `insumos/README.md` sem indicar onde o PDF está guardado.

## 0.4.0 — 23/11/2026
- Revisão de complexidade (D-15). Retirado o reparo automático de JSON com valor ausente (caso nunca reproduzido): resposta inválida para a extração com `ExtractionError`.
- Clima repetido (mesma área e hora): vence a extração mais recente, não mais a maior temperatura (RN-46, teste novo).
- Removida a variável `AREAS_FILE`, que não estava documentada; `assert` trocado em `quality.py`; cálculo do último dia de clima reescrito para leitura.
- README: tabela de qualidade completa (todas as faixas e limites de nulos do contrato). `requisitos.md`: RNF-07 atualizado.
- Conferido: 43 testes passando; execução completa com Parquet idênticos byte a byte aos versionados.
- Mantidos (P-10): variáveis de ajuste HTTP, chave opcional do Open-Meteo e bloqueio por carga MMGD fora da faixa, este com fonte no dicionário do ONS (`val_cargammgd` não permite negativo).

## 0.3.3 — 23/11/2026
- RNF-12 validado: clone do GitHub no Windows, seguindo só o README: `43 passed` e execução completa `success_with_warnings` (41 de 42), com Parquet idênticos byte a byte aos versionados (DT-02).
- README: URL real no `git clone`, comando de testes para Windows e Linux, Python testado no Windows.

## 0.3.2 — 23/11/2026
- `run.ps1` testado no Windows (DT-03) e corrigido: não para mais com saída redirecionada (`2>&1`); `--areas PA,SP` chega inteiro ao pipeline; falha do `venv` ou do `pip` interrompe o script.
- README e `CLAUDE.md`: teste rápido com `OUTPUT_DIR`/`RAW_DIR` em `data/teste-rapido/`, sem sobrescrever o `output/` versionado (DT-16 mitigado).

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
- Projeto organizado em pasta local (62 arquivos).
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
