# Roadmap e cronograma

Versão 1.0 · 12/11/2026

Estratégia: primeiro um fluxo completo e pequeno, depois endurecer. O último dia fica
reservado para correções, não para implementação.

## Cronograma
| Data | Foco | Resultado esperado | Situação em 12/11 |
|---|---|---|---|
| 12/11 | Requisitos e tema | Matriz de aceite e pergunta do projeto | Concluído |
| 13/11 | Validação das APIs | Amostras reais e JOIN viável | Concluído (adiantado) |
| 14/11 | Modelagem e estrutura | Schema, regras, repositório base | Concluído (adiantado) |
| 15/11 | Extração | Fontes extraídas | Código concluído; execução real pendente |
| 16/11 | SQL | Desaninhamento, transformações, JOIN | Concluído (adiantado) |
| 17/11 | Fluxo completo | Primeira execução ponta a ponta | **Pendente com as APIs reais** |
| 18/11 | Qualidade | Validações e relatório | Concluído (adiantado) |
| 19/11 | Resiliência e reprocessamento | Falhas tratadas, reexecução segura | Concluído em teste |
| 20/11 | Testes | Cenários principais automatizados | Concluído (43 testes) |
| 21/11 | Documentação | README e execução em ambiente limpo | Documentação concluída; clone limpo no Windows validado em 23/11/2026 |
| 22/11 | Revisão final | Artefatos conferidos, versão de entrega | Pendente |
| 23/11 antes das 08h00 | Submissão | Link enviado pelo formulário | Pendente |

## Caminho crítico restante
1. Execução real (P-01) → 2. conferência do `output/` → 3. repositório público (P-02) →
4. clone limpo → 5. envio do link (P-03).

Como o desenvolvimento foi adiantado, há folga de vários dias. Recomenda-se fazer os passos
1 a 4 até 17/11 e usar o restante para revisão.

## Evoluções possíveis depois da entrega (fora do escopo)
- Coordenada ponderada pela carga ou pela população em vez do centróide da UF.
- Áreas compostas (ALPE, PBRN, BASE) com mais de uma coordenada.
- Carga programada do ONS (`/cargaprogramada`) para comparar previsto × verificado.
- Análise estatística e painel sobre o dataset.
