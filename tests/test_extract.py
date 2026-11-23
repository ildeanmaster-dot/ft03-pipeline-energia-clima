"""Extração: janelas, leitura do JSON, truncamento silencioso do ONS e validação de formato."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

import pytest

from conftest import holidays_payload, ons_records, open_meteo_payload
from pipeline import extract
from pipeline.config import Settings
from pipeline.extract import ExtractionError, SourceStats, fetch_ons_window, month_windows, parse_json


def test_month_windows_nao_cruza_virada_de_mes() -> None:
    assert month_windows(date(2026, 8, 15), date(2026, 10, 3)) == [
        (date(2026, 8, 15), date(2026, 8, 31)),
        (date(2026, 9, 1), date(2026, 9, 30)),
        (date(2026, 10, 1), date(2026, 10, 3)),
    ]
    assert month_windows(date(2026, 12, 31), date(2027, 1, 1)) == [
        (date(2026, 12, 31), date(2026, 12, 31)),
        (date(2027, 1, 1), date(2027, 1, 1)),
    ]


def test_json_valido_e_lido_sem_alteracao() -> None:
    assert parse_json('[{"a": 1}]') == [{"a": 1}]


def test_json_invalido_levanta_erro() -> None:
    with pytest.raises(ExtractionError):
        parse_json("<html>erro</html>")
    with pytest.raises(ExtractionError):  # valor ausente não é reparado: a resposta é recusada
        parse_json('[{"val_cargaglobal": , "x": 1}]')


class TruncatingOnsClient:
    """Imita o ONS: HTTP 200, mas devolve no máximo ``max_days`` dias por resposta."""

    def __init__(self, max_days: int, missing_day: str | None = None) -> None:
        self.max_days = max_days
        self.missing_day = missing_day
        self.calls: list[tuple[str, str]] = []

    def get_text(self, url: str, params: dict[str, str] | None = None) -> str:
        assert params is not None
        self.calls.append((params["dat_inicio"], params["dat_fim"]))
        start, end = date.fromisoformat(params["dat_inicio"]), date.fromisoformat(params["dat_fim"])
        records: list[dict[str, Any]] = []
        day = start
        while day <= end and (day - start).days < self.max_days:
            if day.isoformat() != self.missing_day:
                records += ons_records(params["cod_areacarga"], day)
            day += timedelta(days=1)
        return json.dumps(records)


def test_ons_truncado_em_silencio_e_recuperado_dividindo_a_janela() -> None:
    client = TruncatingOnsClient(max_days=10)
    stats = SourceStats("ons")
    records = fetch_ons_window(client, "PA", date(2026, 10, 1), date(2026, 10, 31), stats)
    days = {record["dat_referencia"] for record in records}
    assert len(days) == 31 and len(records) == 31 * 48
    assert len(client.calls) > 1  # precisou dividir
    assert len({(r["dat_referencia"], r["din_referenciautc"]) for r in records}) == len(records)  # sem duplicar
    assert stats.warnings == []


def test_ons_dia_sem_dado_na_origem_vira_aviso_e_nao_trava() -> None:
    client = TruncatingOnsClient(max_days=99, missing_day="2026-10-03")
    stats = SourceStats("ons")
    records = fetch_ons_window(client, "PA", date(2026, 10, 1), date(2026, 10, 4), stats)
    assert {record["dat_referencia"] for record in records} == {"2026-10-01", "2026-10-02", "2026-10-04"}
    assert any("2026-10-03" in warning for warning in stats.warnings)


def test_ons_registro_sem_campo_obrigatorio_falha() -> None:
    class BadClient:
        def get_text(self, url: str, params: dict[str, str] | None = None) -> str:
            return json.dumps([{"cod_areacarga": "PA"}])

    with pytest.raises(ExtractionError, match="campos obrigatórios"):
        fetch_ons_window(BadClient(), "PA", date(2026, 10, 1), date(2026, 10, 1), SourceStats("ons"))


def test_open_meteo_arrays_de_tamanho_diferente_falham(settings: Settings) -> None:
    payload = open_meteo_payload(date(2026, 10, 11), date(2026, 10, 12))
    payload["hourly"]["temperature_2m"].pop()
    with pytest.raises(ExtractionError, match="temperature_2m"):
        extract.validate_open_meteo(payload, settings.areas[0], date(2026, 10, 11), date(2026, 10, 12))


class RoutingClient:
    """Responde às três APIs com dados de teste e registra os parâmetros recebidos."""

    def __init__(self) -> None:
        self.params: list[dict[str, str]] = []

    def get_text(self, url: str, params: dict[str, str] | None = None) -> str:
        self.params.append(params or {})
        if "ons.org.br" in url:
            assert params is not None
            start, end = date.fromisoformat(params["dat_inicio"]), date.fromisoformat(params["dat_fim"])
            days = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]
            return json.dumps([record for day in days for record in ons_records(params["cod_areacarga"], day)])
        if "open-meteo" in url:
            assert params is not None
            return json.dumps(open_meteo_payload(date.fromisoformat(params["start_date"]), date.fromisoformat(params["end_date"])))
        return json.dumps(holidays_payload())


def test_extracao_grava_envelopes_brutos(settings: Settings) -> None:
    client = RoutingClient()
    extract.reset_raw_dir(settings.raw_dir)
    ons = extract.extract_ons(client, settings)
    meteo = extract.extract_open_meteo(client, settings)
    nager = extract.extract_nager(client, settings)
    assert (ons.files_written, ons.records) == (2, 2 * 2 * 48)
    assert (meteo.files_written, meteo.records) == (2, 2 * 72)  # clima cobre 1 dia a mais (até 13/10)
    assert (nager.files_written, nager.records) == (1, 4)
    envelope = json.loads((settings.raw_dir / "ons" / "PA_2026-10-11_2026-10-12.json").read_text(encoding="utf-8"))
    assert envelope["meta"]["cod_areacarga"] == "PA" and len(envelope["payload"]) == 96
    assert all("apikey" not in params for params in client.params)  # sem chave configurada, nada é enviado
