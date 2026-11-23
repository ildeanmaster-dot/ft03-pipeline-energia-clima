# Riscos

Versão 1.0 · 12/11/2026

Probabilidade e impacto são avaliação do projeto (Alta, Média, Baixa), não medição.

| ID | Risco | Prob. | Impacto | Resposta | Situação |
|---|---|---|---|---|---|
| R-01 | O pipeline falhar na primeira execução com as APIs reais (diferença entre o teste e a API ao vivo) | Média | Alto | Rodar primeiro o teste rápido (1 área, 1 dia); o formato das três respostas já foi conferido com amostras reais | Aberto até P-01 |
| R-02 | API fora do ar ou lenta perto do prazo | Baixa | Alto | Executar e versionar o `output/` com dias de antecedência; `--skip-extract` reaproveita o bruto já baixado | Aberto |
| R-03 | ONS cortar a resposta em silêncio | Alta (confirmado) | Alto | Janela de um mês, conferência dos dias recebidos, divisão automática da janela | Mitigado e testado |
| R-04 | ONS ou Nager.Date bloquearem por excesso de chamadas (limite não publicado) | Baixa | Médio | Intervalo mínimo de 1 s entre chamadas; retentativa com espera crescente e respeito ao `Retry-After` | Mitigado |
| R-05 | ONS devolver JSON inválido quando falta um valor (relato de terceiros, não reproduzido) | Baixa | Médio | A extração para com `ExtractionError` e mensagem clara; o reparo automático foi retirado em 23/11/2026 por tratar um caso não reproduzido | Aceito |
| R-06 | Mudança de formato de uma API | Baixa | Alto | Schema de leitura declarado no SQL: a quebra aparece na leitura, com erro claro | Aceito |
| R-07 | Credencial versionada por engano | Baixa | Alto | `.env` no `.gitignore`; as APIs não exigem chave; conferir o histórico antes de publicar | Mitigado |
| R-08 | Publicar o enunciado marcado "Internal" | Média | Médio | `insumos/*.pdf` no `.gitignore`; item no checklist de entrega | Mitigado |
| R-09 | Centróide da UF representar mal o clima onde a carga se concentra | Alta | Baixo para o desafio | Documentado como limitação; coordenada trocável no CSV | Aceito |
| R-10 | Uso do Open-Meteo ser entendido como comercial | Baixa | Médio | Uso acadêmico; README cita a licença e a restrição | Aceito |
| R-11 | Repositório grande demais com o `output/` versionado | Baixa | Baixo | Medir o tamanho após a execução; reduzir período ou áreas se preciso (P-06) | Aberto |
| R-12 | Perder o prazo de 23/11 08h00 | Baixa | Alto | Desenvolvimento adiantado; envio planejado para 22/11 | Aberto |
| R-13 | `duckdb` 2.0.0 não rodar no processador desta máquina (Intel Core i7-870, sem AVX) | Alta no Linux remoto (confirmado); não testada no Windows | Alto | Testar `import duckdb` no Windows; alternativa validada: `duckdb==1.5.6` (43 testes passando) | Aberto (P-08) |