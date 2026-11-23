"""Configuração do pipeline, lida somente de variáveis de ambiente (.env ou os.environ)."""

from __future__ import annotations

import csv
import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ConfigError(ValueError):
    """Configuração inválida ou incompleta."""


@dataclass(frozen=True)
class Area:
    """Área de carga do ONS com a coordenada usada para consultar o clima."""

    cod_areacarga: str
    nome_area: str
    uf: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Settings:
    data_inicio: date
    data_fim: date
    areas: tuple[Area, ...]
    areas_file: Path
    raw_dir: Path
    output_dir: Path
    sql_dir: Path
    http_timeout_connect_s: float
    http_timeout_read_s: float
    http_max_retries: int
    http_backoff_factor: float
    ons_min_interval_s: float
    open_meteo_min_interval_s: float
    nager_min_interval_s: float
    open_meteo_api_key: str | None

    @property
    def dataset_dir(self) -> Path:
        return self.output_dir / "dataset"

    @property
    def reports_dir(self) -> Path:
        return self.output_dir / "reports"


def _parse_date(name: str, value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ConfigError(f"{name} deve estar no formato AAAA-MM-DD; recebido: {value!r}") from exc


def _parse_float(name: str, value: str, minimum: float = 0.0) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise ConfigError(f"{name} deve ser numérico; recebido: {value!r}") from exc
    if number < minimum:
        raise ConfigError(f"{name} deve ser >= {minimum}; recebido: {number}")
    return number


def _resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_areas(areas_file: Path, selected: tuple[str, ...] = ()) -> tuple[Area, ...]:
    """Lê o arquivo de parâmetro de áreas; ``selected`` vazio significa todas."""
    if not areas_file.is_file():
        raise ConfigError(f"Arquivo de áreas não encontrado: {areas_file}")
    with areas_file.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    known = {
        row["cod_areacarga"]: Area(
            cod_areacarga=row["cod_areacarga"],
            nome_area=row["nome_area"],
            uf=row["uf"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
        )
        for row in rows
    }
    if not selected:
        return tuple(known.values())
    unknown = [code for code in selected if code not in known]
    if unknown:
        raise ConfigError(
            f"Áreas sem coordenada em {areas_file.name}: {', '.join(unknown)}. "
            f"Disponíveis: {', '.join(sorted(known))}"
        )
    return tuple(known[code] for code in selected)


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Monta a configuração a partir do ambiente; valores ausentes usam o padrão documentado."""
    source: Mapping[str, str] = os.environ if env is None else env

    def get(name: str, default: str) -> str:
        value = source.get(name, "").strip()
        return value or default

    data_inicio = _parse_date("DATA_INICIO", get("DATA_INICIO", "2026-08-01"))
    data_fim = _parse_date("DATA_FIM", get("DATA_FIM", "2026-10-31"))
    if data_fim < data_inicio:
        raise ConfigError("DATA_FIM não pode ser anterior a DATA_INICIO")

    areas_file = _resolve_path(get("AREAS_FILE", "config/areas_carga.csv"))
    selected = tuple(code.strip().upper() for code in get("AREAS", "").split(",") if code.strip())
    api_key = source.get("OPEN_METEO_API_KEY", "").strip() or None

    return Settings(
        data_inicio=data_inicio,
        data_fim=data_fim,
        areas=load_areas(areas_file, selected),
        areas_file=areas_file,
        raw_dir=_resolve_path(get("RAW_DIR", "data/raw")),
        output_dir=_resolve_path(get("OUTPUT_DIR", "output")),
        sql_dir=PROJECT_ROOT / "sql",
        http_timeout_connect_s=_parse_float("HTTP_TIMEOUT_CONNECT_S", get("HTTP_TIMEOUT_CONNECT_S", "10"), 0.1),
        http_timeout_read_s=_parse_float("HTTP_TIMEOUT_READ_S", get("HTTP_TIMEOUT_READ_S", "60"), 0.1),
        http_max_retries=int(_parse_float("HTTP_MAX_RETRIES", get("HTTP_MAX_RETRIES", "5"))),
        http_backoff_factor=_parse_float("HTTP_BACKOFF_FACTOR", get("HTTP_BACKOFF_FACTOR", "1.0")),
        ons_min_interval_s=_parse_float("ONS_MIN_INTERVAL_S", get("ONS_MIN_INTERVAL_S", "1.0")),
        open_meteo_min_interval_s=_parse_float(
            "OPEN_METEO_MIN_INTERVAL_S", get("OPEN_METEO_MIN_INTERVAL_S", "0.5")
        ),
        nager_min_interval_s=_parse_float("NAGER_MIN_INTERVAL_S", get("NAGER_MIN_INTERVAL_S", "1.0")),
        open_meteo_api_key=api_key,
    )
