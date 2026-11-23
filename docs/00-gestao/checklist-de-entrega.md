# Checklist de entrega

Versão 1.0 · 12/11/2026

Marque cada item só depois de conferir a evidência indicada.

## Antes de publicar
- [ ] `pytest` passa (esperado: `43 passed`).
- [ ] Execução completa terminou com `status` igual a `success` ou `success_with_warnings`
      em `output/reports/quality_report.json`.
- [ ] `resumo_verificacoes.falhas_bloqueantes` é `0`.
- [ ] Cada aviso do relatório foi lido e tem explicação.
- [ ] `output/dataset/` tem as pastas `ano=2026/mes=8`, `mes=9` e `mes=10` com arquivos `.parquet`.
- [ ] `dataset.compressao` no relatório é `["SNAPPY"]`.
- [ ] `dataset.linhas_no_dataset` é igual a `linhas_por_etapa.final`
      (esperado com 20 áreas e 92 dias completos: 44.160).
- [ ] Segunda execução do mesmo período não muda `linhas_no_dataset`.
- [ ] `git status` não mostra `.env`, `.venv/`, `data/raw/` nem `insumos/*.pdf`.
- [ ] Busca por credencial no histórico não encontra nada: `git log -p | grep -i -E "apikey|token|password"`.
- [ ] `output/` está versionado (dataset e relatório).
- [ ] Tamanho do repositório é aceitável (P-06).

## Requisitos do enunciado
- [ ] Duas ou mais APIs de domínios distintos, documentadas no README.
- [ ] Controle de taxa e retentativas (código em `src/pipeline/http_client.py`, testes em `tests/test_http_client.py`).
- [ ] Nenhuma credencial no código; `.env.example` presente.
- [ ] Código modular em `src/` com type hints.
- [ ] Desaninhamento feito em SQL (`sql/01_staging.sql`).
- [ ] Cinco transformações identificáveis (`sql/02_transform.sql`, T1 a T5).
- [ ] Validações de schema, null ratio, unicidade e intervalo.
- [ ] Relatório de qualidade em JSON.
- [ ] Parquet com Snappy, particionado por ano/mês, em `output/`.
- [ ] `requirements.txt` e `run.sh`.

## Publicação
- [ ] Repositório criado como **público** no GitHub.
- [ ] Clone em outra pasta + `./run.sh --inicio 2026-10-01 --fim 2026-10-01 --areas PA` funciona seguindo só o README.
- [ ] Link aberto em janela anônima do navegador (confirma que é público).
- [ ] Link enviado pelo formulário antes de **23/11/2026 às 08h00**.
