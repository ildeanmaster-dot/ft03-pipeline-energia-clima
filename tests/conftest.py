"""Fixtures: camada bruta pequena, com o mesmo formato das respostas reais das APIs."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb
import pytest

from pipeline.config import PROJECT_ROOT, Settings, load_settings

SQL_DIR = PROJECT_ROOT / "sql"
AREAS_FILE = PROJECT_ROOT / "config" / "areas_carga.csv"


def ons_records(area: str, day: date, base_load: float = 1000.0, updated: str = "2026-10-31T03:19:26.116Z") -> list[dict[str, Any]]:
    """48 registros semi-horários de um dia de referência (03:30Z até 03:00Z do dia seguinte)."""
    first = datetime(day.year, day.month, day.day, 3, 30)
    records = []
    for index in range(48):
        instant = first + timedelta(minutes=30 * index)
        load = base_load + index
        records.append(
            {
                "cod_areacarga": area,
                "din_atualizacao": updated,
                "dat_referencia": day.isoformat(),
                "din_referenciautc": instant.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "val_cargaglobal": load,
                "val_cargaglobalcons": load,
                "val_cargaglobalsmmgd": load - 10.0,
                "val_cargasupervisionada": load - 50.0,
                "val_carganaosupervisionada": 40.0,
                "val_cargammgd": 10.0,
                "val_consistencia": 0,
            }
        )
    return records


def open_meteo_payload(start: date, end: date, temperature: float = 28.0) -> dict[str, Any]:
    hours = ((end - start).days + 1) * 24
    first = datetime(start.year, start.month, start.day)
    return {
        "latitude": -3.97,
        "longitude": -53.1,
        "elevation": 100.0,
        "timezone": "GMT",
        "hourly_units": {"time": "iso8601", "temperature_2m": "°C"},
        "hourly": {
            "time": [(first + timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(hours)],
            "temperature_2m": [temperature + (h % 24) / 10 for h in range(hours)],
            "relative_humidity_2m": [70.0] * hours,
            "apparent_temperature": [temperature + 2.0] * hours,
            "precipitation": [0.0] * hours,
        },
    }


def holidays_payload() -> list[dict[str, Any]]:
    base = {"countryCode": "BR", "fixed": False, "launchYear": None, "types": ["Public"]}
    return [
        {**base, "date": "2026-10-12", "localName": "Nossa Senhora Aparecida", "name": "Our Lady of Aparecida", "global": True, "counties": None},
        {**base, "date": "2026-07-09", "localName": "Revolução Constitucionalista de 1932", "name": "Constitutionalist Revolution", "global": False, "counties": ["BR-SP"]},
        # Dois feriados no mesmo dia para SP: não pode multiplicar linhas no JOIN.
        {**base, "date": "2026-10-12", "localName": "Feriado estadual fictício de teste", "name": "Test", "global": False, "counties": ["BR-SP", "BR-RJ"]},
        {**base, "date": "2026-10-28", "localName": "Dia do Servidor (não público)", "name": "Optional", "global": True, "counties": None, "types": ["Optional"]},
    ]


def write_envelope(path: Path, meta: dict[str, Any], payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"meta": {**meta, "extraido_em": "2026-11-12T08:00:00+00:00"}, "payload": payload}), encoding="utf-8")


def build_raw(raw_dir: Path, areas: tuple[str, ...] = ("PA", "SP"), start: date = date(2026, 10, 11), end: date = date(2026, 10, 12)) -> Path:
    """Monta data/raw com 2 áreas x 2 dias (o dia 12/10 é feriado nacional)."""
    for area in areas:
        records: list[dict[str, Any]] = []
        day = start
        while day <= end:
            records += ons_records(area, day)
            day += timedelta(days=1)
        write_envelope(raw_dir / "ons" / f"{area}_{start}_{end}.json", {"cod_areacarga": area, "dat_inicio": str(start), "dat_fim": str(end)}, records)
        # o clima cobre um dia a mais porque o dia de referência termina às 03:00Z do dia seguinte
        write_envelope(
            raw_dir / "open_meteo" / f"{area}_{start}_{end}.json",
            {"cod_areacarga": area, "latitude_solicitada": -3.98, "longitude_solicitada": -53.07, "dat_inicio": str(start), "dat_fim": str(end)},
            open_meteo_payload(start, end + timedelta(days=1)),
        )
    write_envelope(raw_dir / "nager" / "BR_2026.json", {"ano": 2026, "pais": "BR"}, holidays_payload())
    return raw_dir


@pytest.fixture
def raw_dir(tmp_path: Path) -> Path:
    return build_raw(tmp_path / "raw")


@pytest.fixture
def con() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return load_settings(
        {
            "DATA_INICIO": "2026-10-11",
            "DATA_FIM": "2026-10-12",
            "AREAS": "PA,SP",
            "RAW_DIR": str(tmp_path / "raw"),
            "OUTPUT_DIR": str(tmp_path / "output"),
            "ONS_MIN_INTERVAL_S": "0",
            "OPEN_METEO_MIN_INTERVAL_S": "0",
            "NAGER_MIN_INTERVAL_S": "0",
        }
    )
