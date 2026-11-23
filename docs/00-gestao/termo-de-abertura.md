# Termo de abertura do projeto

Versão 1.1 · 23/11/2026

## 1. Identificação
| Item | Valor |
|---|---|
| Projeto | Desafio Python – FT03 – Projeto 1: pipeline carga de energia × clima × feriados |
| Responsável | Ildean Freitas |
| Origem | Enunciado `FT03_Engenharia_PRJ01_Python.pdf` (ver `insumos/README.md`) |
| Início | 12/11/2026 |
| Prazo de entrega | 23/11/2026 às 08h00 |
| Forma de entrega | Link de repositório público no GitHub, enviado pelo formulário que será apresentado [link a receber] |

## 2. Contexto
O enunciado avalia a capacidade de estruturar e implementar um pipeline resiliente de
extração, transformação e disponibilização de dados com Python e SQL, simulando a rotina de
Engenharia de Dados.

## 3. Objetivo
Entregar um pipeline reproduzível que consome APIs públicas de domínios distintos, desaninha
e transforma os dados em SQL, valida a qualidade e grava um dataset colunar particionado,
respondendo à pergunta: **como temperatura e umidade se relacionam com a carga de energia
elétrica por área e por hora, e se feriados alteram esse padrão.**

## 4. Escopo
**Dentro**
- Extração de três APIs públicas: ONS (carga verificada), Open-Meteo (clima histórico), Nager.Date (feriados).
- Controle de taxa, retentativas e tratamento de erro na extração.
- Desaninhamento em SQL e as cinco transformações obrigatórias.
- Validações de qualidade e relatório em JSON.
- Dataset em Parquet com Snappy, particionado por ano/mês.
- Testes automatizados, README, `requirements.txt`, execução em um comando.

**Fora**
- Painel, visualização ou análise estatística da relação carga × clima.
- Orquestrador, agendamento, nuvem, processamento distribuído.
- Áreas de carga que não correspondem a uma única UF (submercados, áreas compostas, perdas).
- Feriados municipais.

## 5. Entregas e critério de aceite
| # | Entrega | Critério de aceite (do enunciado) |
|---|---|---|
| E1 | Repositório Git | Código versionado, estrutura modular em `src/`, público no GitHub |
| E2 | `README.md` | Instruções de execução, variáveis de ambiente, documentação das APIs |
| E3 | `requirements.txt` | Bibliotecas necessárias para reprodução exata |
| E4 | Executável | `run.sh` ou comando único para execução ponta a ponta |
| E5 | Dataset persistido | Dados finais limpos e particionados em `output/` (.parquet) |
| E6 | Relatório de qualidade | Resultado das validações e métricas de consistência, em JSON ou CSV |

Critérios de avaliação do enunciado: engenharia de software, qualidade técnica, robustez e governança.

## 6. Premissas
- As três APIs continuam abertas, sem chave, até a entrega.
- O uso é acadêmico e não comercial (condição do plano gratuito do Open-Meteo).
- A execução real acontece no computador do responsável, com acesso à internet.

## 7. Restrições
- Prazo fixo: 23/11/2026 às 08h00.
- Repositório precisa ser público; nenhuma credencial pode ser versionada.
- O PDF do enunciado tem a marca "Internal" e não deve ser publicado.

## 8. Riscos principais
Ver `docs/00-gestao/riscos.md`. Os três maiores: o pipeline ainda não rodou com as APIs reais (resolvido em 23/11/2026);
indisponibilidade de uma API perto do prazo; resposta do ONS cortada em silêncio.

## 9. Marcos
| Marco | Data planejada | Situação |
|---|---|---|
| Requisitos e pergunta de negócio | 12/11 | Concluído |
| APIs escolhidas e validadas em chamada real | 13/11 | Concluído em 12/11 |
| Código, SQL, qualidade, testes e documentação | 14 a 21/11 | Concluído em 12/11 |
| Primeira execução com as APIs reais | 17/11 | Concluído em 23/11 |
| Repositório público com `output/` | 22/11 | Concluído em 23/11 |
| Envio do link | 23/11 antes das 08h00 | Pendente |

## 10. Partes interessadas
| Parte | Papel |
|---|---|
| Ildean Freitas | Responsável pela entrega |
| Avaliadores do desafio FT03 | Avaliam o repositório [nomes não informados] |