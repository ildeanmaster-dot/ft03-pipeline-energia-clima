"""Persistência (Parquet Snappy particionado, idempotente) e execução ponta a ponta."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import duckdb

from conftest import AREAS_FILE, SQL_DIR, build_raw
from pipeline import main as pipeline_main
from pipeline.config import Settings
from pipeline.persist import verify_dataset, write_partitioned
from pipeline.transform import FINAL_TABLE, run_transformations


def read_all(con: duckdb.DuckDBPyConnection, dataset_dir: Path) -> list[tuple]:
    return con.execute(
        f"SELECT cod_areacarga, hora_utc, carga_media_mw, ano, mes FROM read_parquet('{dataset_dir.as_posix()}/**/*.parquet', hive_partitioning = true) ORDER BY 1, 2"
    ).fetchall()


def test_parquet_particionado_snappy(con: duckdb.DuckDBPyConnection, raw_dir: Path, tmp_path: Path) -> None:
    run_transformations(con, raw_dir, AREAS_FILE, SQL_DIR)
    dataset_dir = tmp_path / "dataset"
    partitions = write_partitioned(con, FINAL_TABLE, dataset_dir)
    assert [(p["ano"], p["mes"], p["linhas"]) for p in partitions] == [(2026, 10, 96)]
    assert list((dataset_dir / "ano=2026" / "mes=10").glob("*.parquet"))
    assert verify_dataset(con, dataset_dir) == {"linhas_no_dataset": 96, "compressao": ["SNAPPY"]}


def test_reexecucao_nao_duplica_e_preserva_outras_particoes(con: duckdb.DuckDBPyConnection, tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset"
    # 1ª carga: setembro
    run_transformations(con, build_raw(tmp_path / "raw_set", start=date(2026, 9, 10), end=date(2026, 9, 11)), AREAS_FILE, SQL_DIR)
    write_partitioned(con, FINAL_TABLE, dataset_dir)
    # 2ª e 3ª cargas: outubro, duas vezes com a mesma entrada
    raw_out = build_raw(tmp_path / "raw_out")
    run_transformations(con, raw_out, AREAS_FILE, SQL_DIR)
    write_partitioned(con, FINAL_TABLE, dataset_dir)
    first = read_all(con, dataset_dir)
    run_transformations(con, raw_out, AREAS_FILE, SQL_DIR)
    write_partitioned(con, FINAL_TABLE, dataset_dir)
    second = read_all(con, dataset_dir)
    assert first == second  # mesmas chaves e métricas
    assert len(second) == 96 + 96  # setembro preservado + outubro sem duplicar
    assert len({(row[0], row[1]) for row in second}) == len(second)


def test_pipeline_ponta_a_ponta_gera_dataset_e_relatorio(settings: Settings) -> None:
    build_raw(settings.raw_dir)
    report = pipeline_main.run_pipeline(settings, skip_extract=True)
    assert report["status"] == "success"
    assert report["linhas_por_etapa"]["final"] == 96
    assert report["dataset"] == {"linhas_no_dataset": 96, "compressao": ["SNAPPY"]}
    saved = json.loads((settings.reports_dir / "quality_report.json").read_text(encoding="utf-8"))
    assert saved["run_id"] == report["run_id"] and saved["resumo_verificacoes"]["falhas_bloqueantes"] == 0
    assert {"null_ratio_por_coluna", "verificacoes", "particoes_gravadas", "duracao_s"} <= saved.keys()


def test_falha_de_qualidade_bloqueia_publicacao_mas_grava_relatorio(settings: Settings, monkeypatch) -> None:
    build_raw(settings.raw_dir)
    original = pipeline_main.transform.run_transformations

    def with_duplicates(con, *args):
        counts = original(con, *args)
        con.execute(f"INSERT INTO {FINAL_TABLE} SELECT * FROM {FINAL_TABLE} LIMIT 1")
        return counts

    monkeypatch.setattr(pipeline_main.transform, "run_transformations", with_duplicates)
    report = pipeline_main.run_pipeline(settings, skip_extract=True)
    assert report["status"] == "failed_quality"
    assert not settings.dataset_dir.exists()  # nada publicado
    assert (settings.reports_dir / "quality_report.json").is_file()


def test_erro_na_extracao_grava_relatorio_com_status_failed(settings: Settings, monkeypatch) -> None:
    def broken(_settings):
        raise RuntimeError("API fora do ar")

    monkeypatch.setattr(pipeline_main, "run_extraction", broken)
    report = pipeline_main.run_pipeline(settings)
    assert report["status"] == "failed" and "API fora do ar" in report["erros"][0]
    assert (settings.reports_dir / "quality_report.json").is_file()
