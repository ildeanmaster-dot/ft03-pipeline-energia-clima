# Visão geral (para quem não é da área técnica)

Versão 1.0 · 12/11/2026

## O que este projeto faz
Ele junta, de forma automática, três informações públicas sobre o Brasil e entrega uma única
tabela organizada, pronta para análise:

1. **Quanto de energia elétrica cada estado consumiu**, hora a hora — do Operador Nacional do
   Sistema Elétrico (ONS).
2. **Como estava o tempo** naquela hora (temperatura, umidade, sensação térmica, chuva) — do
   serviço Open-Meteo.
3. **Se o dia era feriado** — do serviço Nager.Date.

## A pergunta que a tabela ajuda a responder
> Quando esquenta, o consumo de energia sobe? Quanto? E nos feriados, o padrão muda?

O projeto **não responde** a pergunta: ele prepara os dados para que ela possa ser
respondida com confiança. É o trabalho de base que vem antes de qualquer gráfico ou análise.

## Como funciona, em quatro passos
1. **Buscar.** O programa pede os dados aos três serviços, com cuidado para não sobrecarregar
   nenhum deles e tentando de novo quando há falha passageira.
2. **Organizar.** Os dados chegam em formatos diferentes (um de meia em meia hora, outro em
   listas, outro por dia). O programa coloca tudo na mesma medida: uma linha por estado e por hora.
3. **Conferir.** Antes de entregar, o programa verifica se há linha repetida, valor faltando
   ou número absurdo (por exemplo, temperatura de 99 °C). Se houver problema grave, ele
   **não publica** a tabela e explica o motivo num relatório.
4. **Guardar.** A tabela é gravada em arquivos compactos, separados por ano e mês, e
   acompanhada de um relatório de qualidade.

## O que sai no final
- **A tabela** (`output/dataset/`): para cada estado e cada hora, a carga de energia, o clima,
  se era feriado, o dia da semana e três indicadores calculados:
  - participação da geração própria dos consumidores (painéis solares, principalmente) na carga;
  - variação do consumo em relação à mesma hora do dia anterior;
  - se era fim de semana.
- **O relatório de qualidade** (`output/reports/quality_report.json`): quantos dados foram
  buscados, quantos foram descartados e por quê, e o resultado de cada conferência.

## Alcance
- **Onde:** 20 estados (os que o ONS trata como uma área própria). Ficam de fora os estados
  que o ONS agrupa, como Alagoas com Pernambuco e Bahia com Sergipe.
- **Quando:** de 1º de agosto a 31 de outubro de 2026, por padrão. O período pode ser trocado.

## Cuidados que tomamos
- **Nada é inventado.** Quando um dado não existe na fonte, o campo fica vazio; não é
  preenchido com estimativa.
- **Tudo tem origem registrada.** Cada coluna da tabela diz de onde veio ou como foi calculada.
- **Nenhuma senha no projeto.** Os três serviços são abertos e não exigem cadastro.

## Limites que é bom conhecer
- O clima de cada estado é medido num único ponto, o centro geográfico do estado. Em estados
  grandes, esse ponto pode ficar longe de onde a maior parte das pessoas mora.
- Feriados municipais não entram.
- O uso gratuito do serviço de clima vale só para fins não comerciais.

## Situação
O programa está pronto e testado com amostras reais. Falta a primeira execução completa com
os três serviços e a publicação. Detalhes em `docs/00-gestao/estado-do-projeto.md`.
