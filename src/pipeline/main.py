"""Orquestra o pipeline ponta a ponta: extração -> SQL -> qualidade -> Parquet -> relatório."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

import duckdb
from dotenv import load_dotenv

from pipeline import extract, persist, quality, transform
from pipeline.config import PROJECT_ROOT, ConfigError, Settings, load_settings
from pipeline.http_client import HttpClient

logger = logging.getLogger("pipeline")

REPORT_NAME = "quality_report.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_client(name: str, min_interval_s: float, settings: Settings) -> HttpClient:
    return HttpClient(
        name,
        min_interval_s=min_interval_s,
        timeout_s=(settings.http_timeout_connect_s, settings.http_timeout_read_s),
        max_retries=settings.http_max_retries,
        backoff_factor=settings.http_backoff_factor,
    )


def run_extraction(settings: Settings) -> dict[str, Any]:
    """Extrai as três fontes e devolve as estatísticas por fonte para o relatório."""
    extract.reset_raw_dir(settings.raw_dir)
    jobs = (
        ("ons", settings.ons_min_interval_s, extract.extract_ons),
        ("open_meteo", settings.open_meteo_min_interval_s, extract.extract_open_meteo),
        ("nager", settings.nager_min_interval_s, extract.extract_nager),
    )
    summary: dict[str, Any] = {}
    for name, interval, job in jobs:
        client = build_client(name, interval, settings)
        stats = job(client, settings)
        summary[name] = {
            "requisicoes": client.stats.requests,
            "retentativas": client.stats.retries,
            "bytes_recebidos": client.stats.bytes_received,
            "espera_rate_limit_s": round(client.rate_limit_wait_s, 2),
            "arquivos_brutos": stats.files_written,
            "registros": stats.records,
            "avisos": stats.warnings,
        }
    return summary


def write_report(settings: Settings, report: dict[str, Any]) -> None:
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    path = settings.reports_dir / REPORT_NAME
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    logger.info("Relatório de qualidade gravado em %s", path)


def run_pipeline(settings: Settings, skip_extract: bool = False) -> dict[str, Any]:
    """Executa todas as etapas; o relatório é gravado mesmo quando uma etapa falha."""
    started = _now()
    report: dict[str, Any] = {
        "run_id": uuid.uuid4().hex[:12],
        "status": "running",
        "inicio_utc": started.isoformat(timespec="seconds"),
        "periodo": {"data_inicio": settings.data_inicio.isoformat(), "data_fim": settings.data_fim.isoformat()},
        "areas": [area.cod_areacarga for area in settings.areas],
        "extracao": "reaproveitada (--skip-extract)" if skip_extract else {},
        "linhas_por_etapa": {},
        "null_ratio_por_coluna": {},
        "verificacoes": [],
        "resumo_verificacoes": {},
        "particoes_gravadas": [],
        "dataset": {},
        "erros": [],
    }
    con = duckdb.connect(":memory:")
    try:
        if not skip_extract:
            report["extracao"] = run_extraction(settings)
        report["linhas_por_etapa"] = transform.run_transformations(
            con, settings.raw_dir, settings.areas_file, settings.sql_dir
        )
        results, ratios = quality.run_quality_checks(con, transform.FINAL_TABLE, report["areas"])
        report["null_ratio_por_coluna"] = ratios
        report["verificacoes"] = [result.to_dict() for result in results]
        failed = [result for result in results if not result.passed]
        report["resumo_verificacoes"] = {
            "total": len(results),
            "aprovadas": len(results) - len(failed),
            "falhas_bloqueantes": sum(1 for result in failed if result.severity == "error"),
            "avisos": sum(1 for result in failed if result.severity == "warning"),
        }
        if quality.has_blocking_failure(results):
            report["status"] = "failed_quality"
            report["erros"].append("Verificação bloqueante falhou: dataset NÃO publicado.")
        else:
            report["particoes_gravadas"] = persist.write_partitioned(con, transform.FINAL_TABLE, settings.dataset_dir)
            report["dataset"] = persist.verify_dataset(con, settings.dataset_dir)
            report["status"] = "success_with_warnings" if failed else "success"
    except Exception as exc:  # o relatório precisa registrar qualquer falha antes de sair
        logger.exception("Pipeline interrompido")
        report["status"] = "failed"
        report["erros"].append(f"{type(exc).__name__}: {exc}")
    finally:
        con.close()
        finished = _now()
        report["fim_utc"] = finished.isoformat(timespec="seconds")
        report["duracao_s"] = round((finished - started).total_seconds(), 2)
        write_report(settings, report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline carga de energia x clima x feriados")
    parser.add_argument("--inicio", help="Data inicial AAAA-MM-DD (sobrepõe DATA_INICIO)")
    parser.add_argument("--fim", help="Data final AAAA-MM-DD (sobrepõe DATA_FIM)")
    parser.add_argument("--areas", help="Áreas separadas por vírgula (sobrepõe AREAS)")
    parser.add_argument("--skip-extract", action="store_true", help="Reaproveita data/raw sem chamar as APIs")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = parse_args(argv)
    load_dotenv(PROJECT_ROOT / ".env")
    env = dict(os.environ)
    for name, value in (("DATA_INICIO", args.inicio), ("DATA_FIM", args.fim), ("AREAS", args.areas)):
        if value:
            env[name] = value
    try:
        settings = load_settings(env)
    except ConfigError as exc:
        logger.error("Configuração inválida: %s", exc)
        return 2
    report = run_pipeline(settings, skip_extract=args.skip_extract)
    logger.info("Status final: %s | verificações: %s", report["status"], report["resumo_verificacoes"])
    return 0 if report["status"].startswith("success") else 1


if __name__ == "__main__":
    sys.exit(main())
