"""Executa os arquivos SQL (DuckDB) sobre a camada bruta e devolve contagens por etapa."""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

logger = logging.getLogger(__name__)

SQL_FILES: tuple[str, ...] = ("01_staging.sql", "02_transform.sql")
FINAL_TABLE = "carga_clima_horaria"
STAGE_TABLES: dict[str, str] = {
    "ons_arquivos_brutos": "raw_ons",
    "ons_registros_apos_unnest": "stg_ons",
    "ons_rejeitados_por_nulo": "rejeitados_ons",
    "ons_apos_tratamento_nulos": "t2_ons",
    "ons_apos_deduplicacao": "t3_ons",
    "ons_horas_agregadas": "carga_horaria",
    "clima_arquivos_brutos": "raw_clima",
    "clima_horas_apos_unnest": "stg_clima",
    "clima_apos_deduplicacao": "t3_clima",
    "feriados_apos_unnest": "stg_feriados",
    "feriados_uf_apos_unnest": "stg_feriados_uf",
    "feriados_por_data_uf": "t3_feriados",
    "apos_join": "t4_cruzado",
    "final": FINAL_TABLE,
}


def run_transformations(
    con: duckdb.DuckDBPyConnection, raw_dir: Path, areas_file: Path, sql_dir: Path
) -> dict[str, int]:
    """Roda staging (UNNEST) e as cinco transformações; devolve linhas por etapa."""
    variables = {
        "raw_ons_glob": (raw_dir / "ons" / "*.json").as_posix(),
        "raw_clima_glob": (raw_dir / "open_meteo" / "*.json").as_posix(),
        "raw_feriados_glob": (raw_dir / "nager" / "*.json").as_posix(),
        "areas_file": areas_file.as_posix(),
    }
    for name, value in variables.items():
        con.execute(f"SET VARIABLE {name} = ?", [value])
    for file_name in SQL_FILES:
        logger.info("Executando %s", file_name)
        con.execute((sql_dir / file_name).read_text(encoding="utf-8"))
    return stage_counts(con)


def stage_counts(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for label, table in STAGE_TABLES.items():
        row = con.execute(f"SELECT count(*) FROM {table}").fetchone()
        counts[label] = int(row[0]) if row else 0
    return counts
