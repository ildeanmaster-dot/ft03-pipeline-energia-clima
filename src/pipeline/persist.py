"""Persistência do dataset final em Parquet (Snappy), particionado por ano/mês."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


def write_partitioned(con: duckdb.DuckDBPyConnection, table: str, dataset_dir: Path) -> list[dict[str, Any]]:
    """Grava ``table`` em ``dataset_dir/ano=AAAA/mes=M/`` e devolve as partições gravadas.

    Reprocessamento idempotente: as partições (ano, mês) presentes nesta execução
    são apagadas e regravadas por inteiro; as demais partições não são tocadas.
    ``OVERWRITE`` não é usado porque apaga a raiz inteira (testado no DuckDB 2.0.0).
    """
    partitions = con.execute(
        f"SELECT ano, mes, count(*) FROM {table} GROUP BY ano, mes ORDER BY ano, mes"
    ).fetchall()
    dataset_dir.mkdir(parents=True, exist_ok=True)
    for year, month, _ in partitions:
        shutil.rmtree(dataset_dir / f"ano={year}" / f"mes={month}", ignore_errors=True)

    target = dataset_dir.as_posix().replace("'", "''")
    con.execute(
        f"""
        COPY (SELECT * FROM {table} ORDER BY cod_areacarga, hora_utc)
        TO '{target}'
        (FORMAT parquet, COMPRESSION snappy, PARTITION_BY (ano, mes), OVERWRITE_OR_IGNORE)
        """
    )
    written = []
    for year, month, rows in partitions:
        partition_dir = dataset_dir / f"ano={year}" / f"mes={month}"
        files = sorted(path.name for path in partition_dir.glob("*.parquet"))
        written.append({"ano": year, "mes": month, "linhas": rows, "arquivos": files})
        logger.info("Partição ano=%s/mes=%s gravada: %d linhas", year, month, rows)
    return written


def verify_dataset(con: duckdb.DuckDBPyConnection, dataset_dir: Path) -> dict[str, Any]:
    """Relê o que foi gravado: total de linhas e codecs de compressão encontrados."""
    glob = (dataset_dir / "**" / "*.parquet").as_posix().replace("'", "''")
    rows = con.execute(f"SELECT count(*) FROM read_parquet('{glob}', hive_partitioning = true)").fetchone()
    codecs = con.execute(f"SELECT DISTINCT compression FROM parquet_metadata('{glob}')").fetchall()
    return {"linhas_no_dataset": int(rows[0]) if rows else 0, "compressao": sorted(codec[0] for codec in codecs)}
