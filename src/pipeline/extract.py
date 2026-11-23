"""Extração das três APIs para a camada bruta (data/raw), preservando o retorno original.

Cada arquivo bruto é um envelope ``{"meta": {...}, "payload": <retorno da API>}``:
``meta`` registra o que foi pedido e quando; ``payload`` é o retorno sem alteração.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol

from pipeline.config import Area, Settings

logger = logging.getLogger(__name__)

ONS_URL = "https://apicarga.ons.org.br/prd/cargaverificada"
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_COMMERCIAL_URL = "https://customer-archive-api.open-meteo.com/v1/archive"
NAGER_URL = "https://date.nager.at/api/v3/PublicHolidays/{year}/BR"

ONS_REQUIRED_FIELDS: frozenset[str] = frozenset(
    {"cod_areacarga", "dat_referencia", "din_referenciautc", "val_cargaglobal", "val_cargammgd"}
)
ONS_RECORDS_PER_DAY = 48
HOURLY_VARIABLES: tuple[str, ...] = (
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
)
_MISSING_JSON_VALUE = re.compile(r":\s*(?=[,}\]])")


class ExtractionError(Exception):
    """A resposta da API não tem o formato ou a cobertura esperados."""


class TextClient(Protocol):
    def get_text(self, url: str, params: dict[str, str] | None = None) -> str: ...


@dataclass
class SourceStats:
    """Contadores de uma fonte, levados ao relatório de execução."""

    source: str
    files_written: int = 0
    records: int = 0
    warnings: list[str] = field(default_factory=list)

    def warn(self, message: str) -> None:
        logger.warning("[%s] %s", self.source, message)
        self.warnings.append(message)


def month_windows(start: date, end: date) -> list[tuple[date, date]]:
    """Divide ``[start, end]`` em janelas que não cruzam a virada de mês."""
    windows: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        next_month = (cursor.replace(day=1) + timedelta(days=32)).replace(day=1)
        window_end = min(end, next_month - timedelta(days=1))
        windows.append((cursor, window_end))
        cursor = window_end + timedelta(days=1)
    return windows


def parse_json_tolerant(text: str) -> tuple[Any, bool]:
    """Interpreta JSON; se inválido por valor ausente (``"campo": ,``), troca por ``null``.

    Devolve ``(objeto, reparado)``. Qualquer outro defeito levanta ``ExtractionError``.
    """
    try:
        return json.loads(text), False
    except json.JSONDecodeError:
        repaired = _MISSING_JSON_VALUE.sub(": null", text)
        try:
            return json.loads(repaired), True
        except json.JSONDecodeError as exc:
            raise ExtractionError(f"Resposta não é JSON válido: {exc}") from exc


def write_raw(path: Path, meta: dict[str, Any], payload: Any) -> None:
    """Grava o envelope de forma atômica (arquivo temporário + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    meta = {**meta, "extraido_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump({"meta": meta, "payload": payload}, handle, ensure_ascii=False)
    os.replace(tmp_path, path)


def reset_raw_dir(raw_dir: Path) -> None:
    """Limpa a camada bruta para que a transformação veja só a execução atual."""
    for source in ("ons", "open_meteo", "nager"):
        shutil.rmtree(raw_dir / source, ignore_errors=True)
        (raw_dir / source).mkdir(parents=True, exist_ok=True)


def _days(start: date, end: date) -> set[str]:
    return {(start + timedelta(days=offset)).isoformat() for offset in range((end - start).days + 1)}


def fetch_ons_window(
    client: TextClient, area: str, start: date, end: date, stats: SourceStats
) -> list[dict[str, Any]]:
    """Busca a carga verificada de uma área, garantindo a cobertura de todos os dias.

    A API devolve HTTP 200 com a resposta cortada quando o período é grande
    (confirmado em 12/11/2026). Por isso, se faltar algum dia pedido, a janela é
    dividida ao meio e buscada de novo, até chegar a um único dia.
    """
    text = client.get_text(
        ONS_URL,
        params={"dat_inicio": start.isoformat(), "dat_fim": end.isoformat(), "cod_areacarga": area},
    )
    payload, repaired = parse_json_tolerant(text)
    if repaired:
        stats.warn(f"JSON com valor ausente reparado (null) em {area} {start}..{end}")
    if not isinstance(payload, list):
        raise ExtractionError(f"ONS {area} {start}..{end}: esperado array JSON, veio {type(payload).__name__}")
    for record in payload:
        if not isinstance(record, dict) or not ONS_REQUIRED_FIELDS <= record.keys():
            raise ExtractionError(
                f"ONS {area} {start}..{end}: registro sem os campos obrigatórios "
                f"{sorted(ONS_REQUIRED_FIELDS)}"
            )

    expected_days = _days(start, end)
    records = [record for record in payload if record["dat_referencia"] in expected_days]
    missing = expected_days - {record["dat_referencia"] for record in records}
    if not missing:
        return records
    if start == end:
        stats.warn(f"ONS sem dados na origem para {area} em {start}")
        return records
    logger.info("ONS %s %s..%s incompleto (%d dia(s) faltando); dividindo a janela", area, start, end, len(missing))
    middle = start + (end - start) // 2
    return fetch_ons_window(client, area, start, middle, stats) + fetch_ons_window(
        client, area, middle + timedelta(days=1), end, stats
    )


def extract_ons(client: TextClient, settings: Settings) -> SourceStats:
    stats = SourceStats("ons")
    for area in settings.areas:
        for start, end in month_windows(settings.data_inicio, settings.data_fim):
            records = fetch_ons_window(client, area.cod_areacarga, start, end, stats)
            per_day: dict[str, int] = {}
            for record in records:
                per_day[record["dat_referencia"]] = per_day.get(record["dat_referencia"], 0) + 1
            partial = sorted(day for day, count in per_day.items() if count != ONS_RECORDS_PER_DAY)
            if partial:
                stats.warn(
                    f"ONS {area.cod_areacarga}: {len(partial)} dia(s) sem {ONS_RECORDS_PER_DAY} "
                    f"registros (ex.: {partial[0]} com {per_day[partial[0]]})"
                )
            write_raw(
                settings.raw_dir / "ons" / f"{area.cod_areacarga}_{start}_{end}.json",
                {"cod_areacarga": area.cod_areacarga, "dat_inicio": start.isoformat(), "dat_fim": end.isoformat()},
                records,
            )
            stats.files_written += 1
            stats.records += len(records)
        logger.info("ONS %s extraído", area.cod_areacarga)
    return stats


def validate_open_meteo(payload: Any, area: Area, start: date, end: date) -> int:
    """Confere o formato da resposta horária e devolve a quantidade de horas."""
    if not isinstance(payload, dict) or not isinstance(payload.get("hourly"), dict):
        raise ExtractionError(f"Open-Meteo {area.cod_areacarga} {start}..{end}: resposta sem o objeto 'hourly'")
    hourly = payload["hourly"]
    times = hourly.get("time")
    if not isinstance(times, list):
        raise ExtractionError(f"Open-Meteo {area.cod_areacarga}: 'hourly.time' ausente")
    for variable in HOURLY_VARIABLES:
        values = hourly.get(variable)
        if not isinstance(values, list) or len(values) != len(times):
            raise ExtractionError(
                f"Open-Meteo {area.cod_areacarga}: array '{variable}' ausente ou com tamanho diferente de 'time'"
            )
    expected_hours = ((end - start).days + 1) * 24
    if len(times) != expected_hours:
        raise ExtractionError(
            f"Open-Meteo {area.cod_areacarga} {start}..{end}: {len(times)} horas, esperado {expected_hours}"
        )
    return len(times)


def extract_open_meteo(client: TextClient, settings: Settings) -> SourceStats:
    stats = SourceStats("open_meteo")
    url = OPEN_METEO_COMMERCIAL_URL if settings.open_meteo_api_key else OPEN_METEO_URL
    # O dia de referência do ONS termina às 03:00 UTC do dia seguinte: o clima
    # precisa cobrir um dia a mais (limitado a hoje) para não faltar nas últimas horas.
    weather_end = min(settings.data_fim + timedelta(days=1), max(settings.data_fim, datetime.now(timezone.utc).date()))
    for area in settings.areas:
        for start, end in month_windows(settings.data_inicio, weather_end):
            params = {
                "latitude": str(area.latitude),
                "longitude": str(area.longitude),
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "hourly": ",".join(HOURLY_VARIABLES),
                "timezone": "UTC",
            }
            if settings.open_meteo_api_key:
                params["apikey"] = settings.open_meteo_api_key
            payload, _ = parse_json_tolerant(client.get_text(url, params=params))
            hours = validate_open_meteo(payload, area, start, end)
            write_raw(
                settings.raw_dir / "open_meteo" / f"{area.cod_areacarga}_{start}_{end}.json",
                {
                    "cod_areacarga": area.cod_areacarga,
                    "latitude_solicitada": area.latitude,
                    "longitude_solicitada": area.longitude,
                    "dat_inicio": start.isoformat(),
                    "dat_fim": end.isoformat(),
                },
                payload,
            )
            stats.files_written += 1
            stats.records += hours
        logger.info("Open-Meteo %s extraído", area.cod_areacarga)
    return stats


def extract_nager(client: TextClient, settings: Settings) -> SourceStats:
    stats = SourceStats("nager")
    for year in range(settings.data_inicio.year, settings.data_fim.year + 1):
        payload, _ = parse_json_tolerant(client.get_text(NAGER_URL.format(year=year)))
        if not isinstance(payload, list) or any("date" not in item for item in payload):
            raise ExtractionError(f"Nager.Date {year}: esperado array de feriados com o campo 'date'")
        if not payload:
            stats.warn(f"Nager.Date sem feriados para {year}")
        write_raw(settings.raw_dir / "nager" / f"BR_{year}.json", {"ano": year, "pais": "BR"}, payload)
        stats.files_written += 1
        stats.records += len(payload)
    return stats
