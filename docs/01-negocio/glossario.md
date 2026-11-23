# Glossário

Versão 1.0 · 12/11/2026

Definições com fonte entre parênteses. Sem fonte indicada = termo geral de engenharia de dados,
explicado para leitura deste projeto.

## Energia
| Termo | Significado |
|---|---|
| ONS | Operador Nacional do Sistema Elétrico, responsável por coordenar e controlar a operação da geração e da transmissão de energia (portal de dados abertos do ONS) |
| Carga | Energia demandada do sistema num intervalo. Neste projeto, o campo `val_cargaglobal` |
| Carga verificada | Carga efetivamente medida, em contraste com a carga programada (Swagger do ONS) |
| MWmed | Megawatt médio: potência média no intervalo. Unidade dos valores de carga (dicionário do ONS) |
| Área de carga | Recorte usado pelo ONS para a carga: submercado, área geoelétrica ou perdas (dicionário do ONS) |
| Área geoelétrica | Tipo de área de carga, em geral nomeada por estado ou grupo de estados (dicionário do ONS) |
| Submercado | Sudeste/Centro-Oeste, Sul, Nordeste e Norte (dicionário do ONS) |
| MMGD | Micro e minigeração distribuída: parcela da carga atendida por geração instalada junto ao consumidor (dicionário do ONS) |
| Carga supervisionada | Parcela atendida por geração supervisionada e intercâmbios, do sistema de supervisão do ONS (Swagger do ONS) |
| Data de referência | Dia a que o registro pertence para o ONS. Vai de 03:30 UTC a 03:00 UTC do dia seguinte (chamada real, 12/11/2026) |
| Semi-horário | De meia em meia hora: 48 registros por dia |

## Clima
| Termo | Significado |
|---|---|
| `temperature_2m` | Temperatura do ar a 2 metros do solo, em °C (unidades na resposta do Open-Meteo) |
| `relative_humidity_2m` | Umidade relativa a 2 metros, em % |
| `apparent_temperature` | Sensação térmica, em °C |
| `precipitation` | Precipitação, em mm |
| Ponto de grade | Ponto do modelo climático mais próximo da coordenada pedida; é a coordenada que o Open-Meteo devolve |
| Centróide | Centro geométrico da UF, informado pela API de Malhas do IBGE |

## Engenharia de dados
| Termo | Significado |
|---|---|
| Pipeline | Sequência automática de etapas: extrair, transformar, validar, gravar |
| Camada bruta | Cópia do que a API devolveu, sem alteração (`data/raw/`) |
| Desaninhar (UNNEST) | Transformar uma lista guardada dentro de um campo em várias linhas |
| Granularidade | O que uma linha representa. Aqui: uma área numa hora |
| Chave | Colunas que identificam uma linha sem repetição: `cod_areacarga` e `hora_utc` |
| Deduplicação | Eliminar registros repetidos, escolhendo qual fica |
| JOIN | Cruzamento de duas tabelas por colunas em comum |
| Null ratio | Fração de valores nulos numa coluna |
| Schema | Lista de colunas e tipos de uma tabela |
| Contrato | Schema e limites que o dataset final precisa cumprir (`CONTRACT` em `quality.py`) |
| Parquet | Formato de arquivo colunar, eficiente para análise |
| Snappy | Algoritmo de compressão usado no Parquet |
| Partição | Subpasta que separa os dados por um critério; aqui `ano=AAAA/mes=M` |
| Partição Hive | Convenção de pastas no formato `coluna=valor` |
| Idempotência | Rodar de novo com a mesma entrada produz o mesmo resultado, sem duplicar |
| Rate limiting | Controle da frequência de chamadas a uma API |
| Backoff exponencial | Espera que cresce a cada nova tentativa |
| Jitter | Variação aleatória somada à espera |
| `Retry-After` | Cabeçalho em que o servidor diz quanto tempo esperar antes de tentar de novo |
| DuckDB | Banco de dados analítico que roda dentro do processo, usado aqui para o SQL |
| Origem / Cálculo / Parâmetro | Classe de cada dado: veio da API; derivado por fórmula; lido de arquivo versionado com fonte |
