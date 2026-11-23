# Custos e licenças

Versão 1.1 · 23/11/2026

O projeto não usa nenhum serviço pago. Este documento registra as condições de uso dos dados
e das bibliotecas.

## 1. APIs
| API | Custo | Chave | Licença dos dados | Restrição | Fonte (consulta em 12/11/2026) |
|---|---|---|---|---|---|
| ONS Carga Verificada | Gratuita | Não | Creative Commons Attribution (CC-BY) | Citar a fonte | https://dados.ons.org.br/dataset/carga-energia-verificada |
| Open-Meteo Historical | Gratuita no plano aberto | Não | CC BY 4.0 | **Só uso não comercial** no plano gratuito; limites de 600/min, 5.000/h, 10.000/dia, 300.000/mês | https://open-meteo.com/en/terms |
| Nager.Date | Gratuita | Não | Código e API sob MIT, segundo terceiros **[a validar na página oficial]** | Limite de taxa não publicado | https://date.nager.at/API |
| IBGE Malhas v4 (só para montar o parâmetro) | Gratuita | Não | Termos de uso não constam na página da API **[a validar]** | Não é chamada pelo pipeline | https://servicodados.ibge.gov.br/api/docs/malhas?versao=4 |

**Atribuição:** o README cita as três fontes com link. Se o projeto deixar de ser acadêmico,
o Open-Meteo exige plano comercial (com chave: variável `OPEN_METEO_API_KEY`).

## 2. Bibliotecas
Licença lida dos metadados de cada pacote instalado, em 12/11/2026.

| Pacote | Versão | Licença | Uso |
|---|---|---|---|
| duckdb | 2.0.0 | MIT | SQL e gravação do Parquet |
| requests | 2.34.2 | Apache-2.0 | Chamadas HTTP |
| urllib3 | 2.8.0 | MIT | Retentativas |
| python-dotenv | 1.2.4 | BSD-3-Clause | Leitura do `.env` |
| pytest | 9.2.0 | MIT | Testes |

## 3. Licença do repositório
**MIT** (decisão do responsável em 23/11/2026, D-16), no arquivo `LICENSE` da raiz. Vale para o
código e a documentação. Os dados em `output/` derivam das fontes e seguem as licenças delas
(ONS: CC-BY; Open-Meteo: CC BY 4.0, uso não comercial no plano gratuito), com citação obrigatória.
