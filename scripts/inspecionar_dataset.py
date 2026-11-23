"""Resumo do dataset gravado em output/dataset (leitura apenas).

Uso: python scripts/inspecionar_dataset.py [pasta_do_dataset]
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "output" / "dataset"


def main(argv: list[str]) -> int:
    dataset_dir = Path(argv[1]) if len(argv) > 1 else DEFAULT_DIR
    files = sorted(dataset_dir.glob("**/*.parquet"))
    if not files:
        print(f"Nenhum arquivo .parquet em {dataset_dir}. Rode o pipeline primeiro.")
        return 1
    glob = (dataset_dir / "**" / "*.parquet").as_posix()
    con = duckdb.connect()
    con.execute(f"CREATE VIEW d AS SELECT * FROM read_parquet('{glob}', hive_partitioning = true)")

    print(f"Pasta: {dataset_dir}\nArquivos: {len(files)}\n")
    print("Partições")
    con.sql("SELECT ano, mes, count(*) AS linhas, min(dat_referencia) AS de, max(dat_referencia) AS ate FROM d GROUP BY ALL ORDER BY ALL").show()
    print("Por área")
    con.sql(
        """
        SELECT cod_areacarga, uf, count(*) AS horas,
               round(avg(carga_media_mw), 1) AS carga_media_mw,
               round(avg(temperatura_c), 1) AS temperatura_media_c,
               round(max(participacao_mmgd_pct), 1) AS mmgd_max_pct,
               count(*) FILTER (WHERE NOT clima_disponivel) AS horas_sem_clima,
               count(DISTINCT dat_referencia) FILTER (WHERE eh_feriado) AS dias_feriado
        FROM d GROUP BY ALL ORDER BY cod_areacarga
        """
    ).show(max_rows=50)
    print("Compressão dos arquivos")
    con.sql(f"SELECT DISTINCT compression FROM parquet_metadata('{glob}')").show()
    duplicated = con.execute(
        "SELECT count(*) FROM (SELECT cod_areacarga, hora_utc FROM d GROUP BY ALL HAVING count(*) > 1)"
    ).fetchone()
    print(f"Chaves repetidas: {duplicated[0] if duplicated else 0}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
