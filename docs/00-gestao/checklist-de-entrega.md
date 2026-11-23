# Checklist de entrega

Versão 1.1 · 23/11/2026

Marque cada item só depois de conferir a evidência indicada. Conferido em 23/11/2026, no Windows
(Python 3.12, duckdb 2.0.0).

## Antes de publicar
- [x] `pytest` passa (esperado: `43 passed`).
- [x] Execução completa terminou com `status` igual a `success` ou `success_with_warnings`
      em `output/reports/quality_report.json` (resultado: `success_with_warnings`).
- [x] `resumo_verificacoes.falhas_bloqueantes` é `0`.
- [x] Cada aviso do relatório foi lido e tem explicação (único aviso: participação MMGD acima de
      100% em 376 horas, valor da fonte; README, seção 9).
- [x] `output/dataset/` tem as pastas `ano=2026/mes=8`, `mes=9` e `mes=10` com arquivos `.parquet`.
- [x] `dataset.compressao` no relatório é `["SNAPPY"]`.
- [x] `dataset.linhas_no_dataset` é igual a `linhas_por_etapa.final`
      (esperado com 20 áreas e 92 dias completos: 44.160).
- [x] Segunda execução do mesmo período não muda `linhas_no_dataset` (os Parquet saíram iguais).
- [x] `git status` não mostra `.env`, `.venv/`, `data/raw/` nem `insumos/*.pdf`.
- [x] Busca por credencial no histórico não encontra nada: `git log -p | grep -i -E "apikey|token|password"`
      (só o valor falso de teste `SEGREDO123`).
- [x] `output/` está versionado (dataset e relatório).
- [x] Tamanho do repositório é aceitável (cerca de 1,7 MB; P-06).

## Requisitos do enunciado
- [x] Duas ou mais APIs de domínios distintos, documentadas no README.
- [x] Controle de taxa e retentativas (código em `src/pipeline/http_client.py`, testes em `tests/test_http_client.py`).
- [x] Nenhuma credencial no código; `.env.example` presente.
- [x] Código modular em `src/` com type hints.
- [x] Desaninhamento feito em SQL (`sql/01_staging.sql`).
- [x] Cinco transformações identificáveis (`sql/02_transform.sql`, T1 a T5).
- [x] Validações de schema, null ratio, unicidade e intervalo.
- [x] Relatório de qualidade em JSON.
- [x] Parquet com Snappy, particionado por ano/mês, em `output/`.
- [x] `requirements.txt` e `run.sh`.

## Publicação
- [x] Repositório criado como **público** no GitHub.
- [x] Clone em outra pasta, seguindo só o README: `43 passed` e execução completa com
      `success_with_warnings`. Para o teste rápido sem alterar o `output/` versionado:
      `OUTPUT_DIR=data/teste-rapido/output RAW_DIR=data/teste-rapido/raw ./run.sh --inicio 2026-10-01 --fim 2026-10-01 --areas PA`
      termina com `Status final: success`, e o `git status` não mostra mudança em `output/`.
- [x] Repositório acessível sem login (conferido pela API pública do GitHub, sem autenticação).
- [ ] Link enviado pelo formulário antes de **23/11/2026 às 08h00**.
