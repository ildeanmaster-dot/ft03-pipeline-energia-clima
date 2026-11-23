"""Qualidade: dataset válido passa; violações intencionais são detectadas."""

from __future__ import annotations

from pathlib import Path

import duckdb

from conftest import AREAS_FILE, SQL_DIR
from pipeline.quality import has_blocking_failure, run_quality_checks
from pipeline.transform import FINAL_TABLE, run_transformations


def prepared(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    run_transformations(con, raw_dir, AREAS_FILE, SQL_DIR)


def by_name(results: list) -> dict:
    return {result.check: result for result in results}


def test_dataset_valido_passa_em_tudo(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    prepared(con, raw_dir)
    results, ratios = run_quality_checks(con, FINAL_TABLE, ["PA", "SP"])
    failed = [result.check for result in results if not result.passed]
    assert failed == []
    assert not has_blocking_failure(results)
    assert ratios["cod_areacarga"] == 0.0 and ratios["variacao_carga_d1_pct"] == 0.5  # 1º dia sem D-1
    dimensions = {result.dimension for result in results}
    assert {"schema", "nulos", "unicidade", "intervalo", "join", "volume", "completude"} <= dimensions


def test_chave_duplicada_bloqueia(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    prepared(con, raw_dir)
    con.execute(f"INSERT INTO {FINAL_TABLE} SELECT * FROM {FINAL_TABLE} LIMIT 3")
    results, _ = run_quality_checks(con, FINAL_TABLE, ["PA", "SP"])
    assert by_name(results)["unicidade_chave"].passed is False
    assert by_name(results)["unicidade_chave"].observed == 3
    assert has_blocking_failure(results)


def test_valor_fora_do_intervalo_e_detectado(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    prepared(con, raw_dir)
    con.execute(f"UPDATE {FINAL_TABLE} SET temperatura_c = 99 WHERE cod_areacarga = 'PA' AND hour(hora_utc) = 5")
    con.execute(f"UPDATE {FINAL_TABLE} SET umidade_relativa_pct = -1 WHERE cod_areacarga = 'SP' AND hour(hora_utc) = 6")
    checks = by_name(run_quality_checks(con, FINAL_TABLE, ["PA", "SP"])[0])
    assert checks["intervalo:temperatura_c"].observed == 2
    assert checks["intervalo:umidade_relativa_pct"].observed == 2
    assert checks["intervalo:precipitacao_mm"].passed


def test_nulo_em_coluna_obrigatoria_bloqueia(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    prepared(con, raw_dir)
    con.execute(f"UPDATE {FINAL_TABLE} SET uf = NULL WHERE cod_areacarga = 'PA'")
    results, ratios = run_quality_checks(con, FINAL_TABLE, ["PA", "SP"])
    assert ratios["uf"] == 0.5
    assert by_name(results)["null_ratio:uf"].passed is False and has_blocking_failure(results)


def test_schema_divergente_e_detectado(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    prepared(con, raw_dir)
    con.execute(f"ALTER TABLE {FINAL_TABLE} DROP COLUMN precipitacao_mm")
    con.execute(f"ALTER TABLE {FINAL_TABLE} ALTER COLUMN qtd_intervalos TYPE VARCHAR")
    schema = by_name(run_quality_checks(con, FINAL_TABLE, ["PA", "SP"])[0])["schema_contrato"]
    assert schema.passed is False
    assert "precipitacao_mm" in schema.detail and "qtd_intervalos" in schema.detail


def test_area_ausente_e_clima_sem_cobertura_viram_aviso(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    (raw_dir / "open_meteo" / "SP_2026-10-11_2026-10-12.json").unlink()
    prepared(con, raw_dir)
    results, _ = run_quality_checks(con, FINAL_TABLE, ["PA", "SP", "RJ"])
    checks = by_name(results)
    assert checks["areas_solicitadas_presentes"].passed is False and "RJ" in checks["areas_solicitadas_presentes"].detail
    assert checks["join_cobertura_clima"].observed == 0.5
    assert checks["join_cobertura_clima"].severity == "warning"
