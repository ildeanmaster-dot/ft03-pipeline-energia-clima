# Segurança e governança

Versão 1.0 · 12/11/2026

## 1. Credenciais
- As três APIs são abertas: **o projeto funciona sem nenhuma chave**.
- A única credencial prevista é opcional: `OPEN_METEO_API_KEY`, para o plano comercial do Open-Meteo.
- Toda configuração é lida do ambiente (`os.environ`, com `.env` carregado por `python-dotenv`),
  em `src/pipeline/config.py`. Não há valor de credencial no código.
- `.env` está no `.gitignore`. `.env.example` é versionado e não contém valor real.
- URLs e mensagens de erro passam por `redact`, que troca o valor de `apikey`, `api_key`,
  `token`, `key` e `access_token` por `***`. Coberto por dois testes.

## 2. O que não vai para o Git
| Item | Motivo | Regra no `.gitignore` |
|---|---|---|
| `.env` | Pode conter chave | `.env` |
| `.venv/`, `venv/` | Ambiente local | `.venv/`, `venv/` |
| `data/raw/` | Reproduzível; volume | `data/raw/` |
| `insumos/*.pdf` | Enunciado com a marca "Internal" | `insumos/*.pdf` |
| Caches | Gerados | `__pycache__/`, `.pytest_cache/` |

## 3. Antes de publicar
1. `git status` e `git ls-files` não listam nenhum item da tabela acima.
2. `git log -p | grep -i -E "apikey|api_key|token|password|secret"` não devolve credencial.
3. Se uma chave tiver sido versionada por engano: **revogar a chave** no provedor. Apagar o
   arquivo num commit novo não remove a chave do histórico.

## 4. Dados publicados
- O dataset contém só dados públicos e agregados (carga por área, clima, feriados). **Não há dado pessoal.**
- Licenças e atribuição: `docs/00-gestao/custos-e-licencas.md`. O README cita as fontes.
- O uso gratuito do Open-Meteo é restrito a fins não comerciais.

## 5. Integridade e rastreabilidade
- Cada arquivo bruto registra o que foi pedido e quando (`meta`).
- Cada coluna do dataset tem classe (Origem, Cálculo, Parâmetro) e fonte no dicionário de dados.
- O parâmetro de áreas traz a fonte em cada linha.
- O relatório registra as contagens por etapa, os rejeitados e o resultado de cada verificação.
- Dataset com falha bloqueante não é publicado.

## 6. Rede
O pipeline só faz requisições GET para três domínios: `apicarga.ons.org.br`,
`archive-api.open-meteo.com` e `date.nager.at`. Com `OPEN_METEO_API_KEY` definida, o Open-Meteo
passa a ser chamado em `customer-archive-api.open-meteo.com` **[endpoint a validar]**.
Não envia dado para lugar nenhum.
